from __future__ import annotations

import logging
import os
import typing
import uuid
from datetime import datetime, timedelta
from typing import Any, List, Mapping, Optional, Type

from bson import ObjectId
from pydantic import BaseModel, Field

from eduid.common.misc.timeutil import utc_now
from eduid.userdb.db import BaseDB
from eduid.userdb.element import ElementKey

if typing.TYPE_CHECKING:
    # avoid circular import
    from eduid.webapp.idp.assurance import EduidAuthnContextClass

logger = logging.getLogger(__name__)


class OtherDevice(BaseModel):
    login_id: str
    short_code: str
    eppn: Optional[str]
    authn_context: Optional['EduidAuthnContextClass']
    reauthn_required: bool
    created_at: datetime
    expires_at: datetime
    obj_id: ObjectId = Field(default_factory=ObjectId, alias='_id')
    response_code: Optional[str] = None
    bad_attempts: int = 0  # number of failed attempts to produce the right response_code
    credentials_used: List[ElementKey] = Field(default=[])  # TODO: doesn't work with onetime_credentials

    class Config:
        # Don't reject ObjectId
        arbitrary_types_allowed = True

    @classmethod
    def from_parameters(
        cls: Type[OtherDevice],
        eppn: Optional[str],
        authn_context: Optional[EduidAuthnContextClass],
        reauthn_required: bool = False,
        ttl: timedelta = timedelta(minutes=20),
    ) -> OtherDevice:
        _uuid = uuid.uuid4()
        short_code = _make_short_code()
        now = utc_now()
        return cls(
            login_id=str(_uuid),
            short_code=short_code,
            eppn=eppn,
            authn_context=authn_context,
            reauthn_required=reauthn_required,
            created_at=now,
            expires_at=now + ttl,
        )

    def to_dict(self) -> Mapping[str, Any]:
        return self.dict()

    @classmethod
    def from_dict(cls: Type[OtherDevice], data: Mapping[str, Any]) -> OtherDevice:
        return cls(**data)


def _make_short_code() -> str:
    digits = int.from_bytes(os.urandom(4), byteorder='big') % 1000000
    return '{:06d}'.format(digits)


class OtherDeviceDB(BaseDB):
    def __init__(self, db_uri: str, db_name: str = 'eduid_idp', collection: str = 'other_device'):
        super().__init__(db_uri, db_name, collection=collection)

        indexes = {
            'auto-discard': {'key': [('expires_at', 1)], 'expireAfterSeconds': 0},
            'unique-session-id': {'key': [('login_id', 1)], 'unique': True},
        }
        self.setup_indexes(indexes)

    def save(self, other: OtherDevice) -> bool:
        """
        Add a new OtherDevice to the database, or update an existing one.
        """
        result = self._coll.replace_one({'_id': other.obj_id}, other.to_dict(), upsert=True)
        logger.debug(
            f'Saved OtherDevice {other} in the db: '
            f'matched={result.matched_count}, modified={result.modified_count}, upserted_id={result.upserted_id}'
        )
        return result.acknowledged

    def get_state_by_login_id(self, login_id: str) -> Optional[OtherDevice]:
        state = self._get_document_by_attr('login_id', str(login_id))
        if not state:
            logger.debug(f'Other-device state with login_id {login_id} not found in the database')
            return None
        return OtherDevice.from_dict(state)
