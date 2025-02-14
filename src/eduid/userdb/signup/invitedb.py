# -*- coding: utf-8 -*-

import datetime
import logging
from dataclasses import replace
from typing import Any, Dict, Optional

from eduid.userdb.exceptions import DocumentOutOfSync, MultipleDocumentsReturned
from eduid.userdb.signup import Invite, SCIMReference
from eduid.userdb.signup.invite import InviteReference
from eduid.userdb.userdb import BaseDB

__author__ = "lundberg"

logger = logging.getLogger(__name__)


class SignupInviteDB(BaseDB):
    def __init__(self, db_uri: str, db_name: str = "eduid_signup", collection: str = "invites"):
        BaseDB.__init__(self, db_uri, db_name, collection)
        # Create an index so that invite_code is unique and invites are removed at the expires_at time
        indexes = {
            "unique-invite-code": {"key": [("invite_code", 1)], "unique": True},
            "auto-discard-expires-at": {
                "key": [("expires_at", 1)],
                "expireAfterSeconds": 0,
            },
        }
        self.setup_indexes(indexes)

    def get_invite_by_invite_code(self, code: str) -> Optional[Invite]:
        doc = self._get_document_by_attr("invite_code", code)
        if doc:
            return Invite.from_dict(doc)
        return None

    def get_invite_by_reference(self, reference: InviteReference) -> Optional[Invite]:
        if isinstance(reference, SCIMReference):
            spec = {"invite_reference.scim_id": reference.scim_id, "invite_reference.data_owner": reference.data_owner}
        else:
            raise NotImplementedError(f"Reference of type {type(reference)} not implemented.")
        docs = self._get_documents_by_filter(spec=spec)
        if len(docs) > 1:
            raise MultipleDocumentsReturned(f"Multiple matching documents for {repr(spec)}")
        elif len(docs) == 1:
            return Invite.from_dict(docs[0])
        return None

    def save(self, invite: Invite, check_sync: bool = True) -> None:
        """
        :param invite: Invite object
        :param check_sync: Ensure the document hasn't been updated in the database since it was loaded
        """
        modified = invite.modified_ts
        invite = replace(invite, modified_ts=datetime.datetime.utcnow())  # update to current time
        if modified is None:
            # document has never been modified
            result = self._coll.insert_one(invite.to_dict())
            logging.debug(f"{self} Inserted new invite {invite} into {self._coll_name}): {result.inserted_id})")
        else:
            test_doc: Dict[str, Any] = {"_id": invite.invite_id}
            if check_sync:
                test_doc["modified_ts"] = modified
            result = self._coll.replace_one(test_doc, invite.to_dict(), upsert=(not check_sync))
            if check_sync and result.matched_count == 0:
                db_ts = None
                db_state = self._coll.find_one({"_id": invite.invite_id})
                if db_state:
                    db_ts = db_state["modified_ts"]
                logging.error(
                    "{} FAILED Updating invite {} (ts {}) in {}). "
                    "ts in db = {!s}".format(self, invite, modified, self._coll_name, db_ts)
                )
                raise DocumentOutOfSync("Stale invite object can't be saved")

            logging.debug(
                "{!s} Updated invite {} (ts {}) in {}): {}".format(self, invite, modified, self._coll_name, result)
            )
