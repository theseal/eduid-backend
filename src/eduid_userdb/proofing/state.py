# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 NORDUnet A/S
# Copyright (c) 2018 SUNET
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

from __future__ import annotations

import bson
import copy
import datetime

from dataclasses import dataclass, asdict

from typing import Optional, Mapping, MutableMapping, Iterable, Set

from eduid_userdb.exceptions import UserDBValueError
from eduid_userdb.proofing.element import NinProofingElement, SentLetterElement
from eduid_userdb.proofing.element import EmailProofingElement, PhoneProofingElement


__author__ = 'lundberg'



@dataclass()
class ProofingState(object):

    # __post_init__ will mint a new ObjectId if `id' is None
    id: Optional[bson.ObjectId]
    eppn: str
    # Timestamp of last modification in the database.
    # None if ProofingState has never been written to the database.
    modified_ts: Optional[datetime.datetime]

    def __post_init__(self):
        if self.id is None:
            self.id = bson.ObjectId()

    @classmethod
    def _default_from_dict(cls, data: Mapping, fields: Set[str]):
        _data = copy.deepcopy(dict(data))  # to not modify callers data
        if 'eduPersonPrincipalName' in _data:
            _data['eppn'] = _data.pop('eduPersonPrincipalName')
        if '_id' in _data:
            _data['id'] = _data.pop('_id')
        fields.update({'id', 'eppn', 'modified_ts'})
        _leftovers = [x for x in _data.keys() if x not in fields]
        if _leftovers:
            raise UserDBValueError(f'{cls}.from_dict() unknown data: {_leftovers}')

        return cls(**_data)

    def to_dict(self) -> MutableMapping:
        res = asdict(self)
        res['_id'] = res.pop('id')
        res['eduPersonPrincipalName'] = res.pop('eppn')
        if res['modified_ts'] == True:
            res['modified_ts'] = datetime.datetime.utcnow()
        return res

    def __str__(self):
        return '<eduID {!s}: eppn={!s}>'.format(self.__class__.__name__, self.eppn)

    @property
    def reference(self) -> str:
        """ Audit reference to help cross reference audit log and events. """
        return str(self.id)

    def is_expired(self, timeout_seconds: int) -> bool:
        """
        Check whether the code is expired.

        :param timeout_seconds: the number of seconds a code is valid
        """
        if not isinstance(self.modified_ts, datetime.datetime):
            if self.modified_ts is True or self.modified_ts is None:
                return False
            raise UserDBValueError(f'Malformed modified_ts: {self.modified_ts!r}')
        delta = datetime.timedelta(seconds=timeout_seconds)
        expiry_date = self.modified_ts + delta
        now = datetime.datetime.now(tz=self.modified_ts.tzinfo)
        return expiry_date < now


@dataclass()
class NinProofingState(ProofingState):

    nin: NinProofingElement

    @classmethod
    def from_dict(cls, data: Mapping) -> NinProofingState:
        _data = copy.deepcopy(dict(data))  # to not modify callers data
        _data['nin'] = NinProofingElement(data=_data['nin'])
        return cls._default_from_dict(_data, {'nin'})

    def to_dict(self) -> MutableMapping:
        res = super().to_dict()
        res['nin'] = res['nin'].to_dict()
        return res


@dataclass()
class LetterProofingState(NinProofingState):

    proofing_letter: SentLetterElement

    @classmethod
    def from_dict(cls, data: Mapping) -> LetterProofingState:
        _data = copy.deepcopy(dict(data))  # to not modify callers data
        _data['nin'] = NinProofingElement(data=_data['nin'])
        _data['proofing_letter'] = SentLetterElement(data=_data['proofing_letter'])
        return cls._default_from_dict(_data, {'nin', 'proofing_letter'})

    def to_dict(self) -> MutableMapping:
        res = super().to_dict()
        res['proofing_letter'] = res['proofing_letter'].to_dict()
        return res


@dataclass()
class OrcidProofingState(ProofingState):

    state: str
    nonce: str

    @classmethod
    def from_dict(cls, data: Mapping) -> OrcidProofingState:
        return cls._default_from_dict(data, {'state', 'nonce'})


@dataclass()
class OidcProofingState(NinProofingState):

    state: str
    nonce: str
    token: str

    @classmethod
    def from_dict(cls, data: Mapping) -> OidcProofingState:
        _data = copy.deepcopy(dict(data))  # to not modify callers data
        _data['nin'] = NinProofingElement(data=_data['nin'])
        return cls._default_from_dict(_data, {'nin', 'state', 'nonce', 'token'})


@dataclass()
class EmailProofingState(ProofingState):

    verification: EmailProofingElement

    @classmethod
    def from_dict(cls, data: Mapping) -> EmailProofingState:
        _data = copy.deepcopy(dict(data))  # to not modify callers data
        _data['verification'] = EmailProofingElement(data=_data['verification'])
        return cls._default_from_dict(_data, {'verification'})

    def to_dict(self) -> MutableMapping:
        res = super().to_dict()
        res['verification'] = res['verification'].to_dict()
        return res


@dataclass()
class PhoneProofingState(ProofingState):

    verification: PhoneProofingElement

    @classmethod
    def from_dict(cls, data: Mapping) -> PhoneProofingState:
        _data = copy.deepcopy(dict(data))  # to not modify callers data
        _data['verification'] = PhoneProofingElement(data=_data['verification'])
        return cls._default_from_dict(_data, {'verification'})

    def to_dict(self) -> MutableMapping:
        res = super().to_dict()
        res['verification'] = res['verification'].to_dict()
        return res
