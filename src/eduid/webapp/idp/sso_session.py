#
# Copyright (c) 2014 NORDUnet A/S
# All rights reserved.
#
#   Redistribution and use in source and binary forms, with or
#   without modification, are permitted provided that the following
#   conditions are met:
#
#     1. Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#     2. Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided
#        with the distribution.
#     3. Neither the name of the NORDUnet nor the names of its
#        contributors may be used to endorse or promote products derived
#        from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Author : Fredrik Thulin <fredrik@thulin.net>
#
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Mapping, NewType, Optional, Type

from bson import ObjectId
from pydantic import BaseModel, Field

from eduid.common.misc.timeutil import utc_now
from eduid.userdb.credentials.base import CredentialKey
from eduid.userdb.idp import IdPUser, IdPUserDb
from eduid.webapp.common.session.logindata import ExternalMfaData
from eduid.webapp.idp.idp_authn import AuthnData

# A distinct type for session ids
SSOSessionId = NewType('SSOSessionId', str)


def create_session_id() -> SSOSessionId:
    """
    Create a unique value suitable for use as session identifier.

    The uniqueness and inability to guess is security critical!
    :return: session_id as bytes (to match what cookie decoding yields)
    """
    return SSOSessionId(str(uuid.uuid4()))


class SSOSession(BaseModel):
    """
    Single Sign On sessions are used to remember a previous authentication
    performed, to avoid re-authenticating users for every Service Provider
    they visit.

    The references to 'authn' here are strictly about what kind of Authn
    the user has performed. The resulting SAML AuthnContext is a product
    of this, as well as other policy decisions (such as what ID-proofing
    has taken place, what AuthnContext the SP requested and so on).

    :param authn_request_id: SAML request id of request that caused authentication
    :param authn_credentials: Data about what credentials were used to authn
    :param authn_timestamp: Authentication timestamp, in UTC

    # These fields are from the 'outer' scope of the session, and are
    # duplicated here for now. Can't be changed here, since they are removed in to_dict.

    :param created_ts: When the database document was created
    :param eppn: User eduPersonPrincipalName

    """

    eppn: str
    authn_credentials: List[AuthnData]
    authn_request_id: str = ''  # This should be obsolete now - used to be used to 'break' forceAuthn looping
    authn_timestamp: datetime = Field(default_factory=utc_now)
    created_ts: datetime = Field(default_factory=utc_now)
    expires_at: datetime = Field(default_factory=lambda: utc_now() + timedelta(minutes=5))
    external_mfa: Optional[ExternalMfaData] = None
    obj_id: ObjectId = Field(default_factory=ObjectId, alias='_id')
    session_id: SSOSessionId = Field(default_factory=create_session_id)

    class Config:
        allow_population_by_field_name = True  # allow setting obj_id by name, not just by it's alias (_id)
        arbitrary_types_allowed = True  # allow ObjectId

    def __str__(self) -> str:
        # Session id allows impersonation if leaked, so only log a small part of it
        short_sessionid = self.session_id[:6] + '...'
        return (
            f'<{self.__class__.__name__}: _id={self.obj_id}, session_id={short_sessionid}, eppn={self.eppn}, '
            f'created={self.created_ts.isoformat()}, authn_ts={self.authn_timestamp.isoformat()}, '
            f'expires_at={self.expires_at.isoformat()}, age={self.age}>'
        )

    def to_dict(self) -> Dict[str, Any]:
        """ Return the object in dict format (serialized for storing in MongoDB).
        """
        res = self.dict()
        res['_id'] = res.pop('obj_id')
        return res

    @classmethod
    def from_dict(cls: Type[SSOSession], data: Mapping[str, Any]) -> SSOSession:
        """ Construct element from a data dict in database format. """
        return cls(**data)

    @property
    def public_id(self) -> str:
        """
        Return a identifier for this session that can't be used to hijack sessions
        if leaked through a log file etc.
        """
        return f'{self.eppn}.{self.created_ts.replace(microsecond=0).isoformat()}'

    @property
    def age(self) -> timedelta:
        """ Return the age of this SSO session, in minutes. """
        return utc_now() - self.authn_timestamp

    def add_authn_credential(self, authn: AuthnData) -> None:
        """ Add information about a credential successfully used in this session. """
        if not isinstance(authn, AuthnData):
            raise ValueError(f'data should be AuthnData (not {type(authn)})')

        # Store only the latest use of a particular credential.
        _creds: Dict[CredentialKey, AuthnData] = {x.cred_id: x for x in self.authn_credentials}
        _existing = _creds.get(authn.cred_id)
        # only replace if newer
        if not _existing or authn.timestamp > _existing.timestamp:
            _creds[authn.cred_id] = authn

        # sort on cred_id to have deterministic order in tests
        _list = list(_creds.values())
        self.authn_credentials = sorted(_list, key=lambda x: x.cred_id)
