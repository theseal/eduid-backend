#
# Copyright (c) 2018 SUNET
# Copyright (c) 2013, 2014, 2016, 2017 NORDUnet A/S
# Copyright 2012 Roland Hedberg. All rights reserved.
# All rights reserved.
#
# See the file eduid-IdP/LICENSE.txt for license statement.
#
# Author : Fredrik Thulin <fredrik@thulin.net>
#          Roland Hedberg
#
import logging
import time
import warnings
from collections import deque
from threading import Lock
from typing import Any, Deque, Dict, List, Mapping, Optional, Tuple, cast

from eduid.userdb.db import BaseDB
from eduid.userdb.exceptions import EduIDDBError
from eduid.webapp.idp.sso_session import SSOSession, SSOSessionId

logger = logging.getLogger(__name__)


class NoOpLock(object):
    """
    A No-op lock class, to avoid a lot of "if self.lock:" in code using locks.
    """

    def __init__(self) -> None:
        pass

    # noinspection PyUnusedLocal
    def acquire(self, _block: bool = True) -> bool:
        """
        Fake acquiring a lock.

        :param _block: boolean, whether to block or not (NO-OP in this implementation)
        """
        return True

    def release(self) -> None:
        """
        Fake releasing a lock.
        """
        pass


class ExpiringCacheMem:
    """
    Simplistic implementation of a cache that removes entrys as they become too old.

    This implementation invokes garbage collecting on every addition of data. This
    is believed to be a pragmatic approach for small to medium sites. For a large
    site with e.g. load balancers causing uneven traffic patterns, this might not
    work that well and the use of an external cache such as memcache is recommended.

    :param name: name of cache as string, only used for debugging
    :param logger: logging logger instance
    :param ttl: data time to live in this cache, as seconds (integer)
    :param lock: threading.Lock compatible locking instance
    """

    def __init__(self, name: str, logger: Optional[logging.Logger], ttl: int, lock: Optional[Lock] = None):
        self.logger = logger
        self.ttl = ttl
        self.name = name
        self._data: Dict[SSOSessionId, Any] = {}
        self._ages: Deque[Tuple[float, SSOSessionId]] = deque()
        self.lock = lock
        if self.lock is None:
            self.lock = cast(Lock, NoOpLock())  # intentionally lie to mypy

        if self.logger is not None:
            warnings.warn("Object logger deprecated, using module_logger", DeprecationWarning)

    def add(self, key: SSOSessionId, info: Any, now: Optional[int] = None) -> None:
        """
        Add entry to the cache.

        Ability to supply current time is only meant for test cases!

        :param key: Lookup key for entry
        :param info: Value to be stored for 'key'
        :param now: Current time - do not use unless testing!
        """
        self._data[key] = info
        # record when this entry shall be purged
        _now = now
        if _now is None:
            _now = int(time.time())
        self._ages.append((_now, key))
        self._purge_expired(_now - self.ttl)

    def _purge_expired(self, timestamp: int) -> None:
        """
        Purge expired records.

        :param timestamp: Purge any entrys older than this (integer)
        """
        if not self.lock or not self.lock.acquire(False):
            # if we don't get the lock, don't worry about it and just skip purging
            return None
        try:
            # purge any expired records. self._ages have the _data entries listed with oldest first.
            while True:
                try:
                    (_exp_ts, _exp_key) = self._ages.popleft()
                except IndexError:
                    break
                if _exp_ts > timestamp:
                    # entry not expired - reinsert in queue and end purging
                    self._ages.appendleft((_exp_ts, _exp_key))
                    break
                logger.debug(
                    "Purged {!s} cache entry {!s} seconds over limit : {!s}".format(
                        self.name, timestamp - _exp_ts, _exp_key
                    )
                )
                self.delete(_exp_key)
        finally:
            self.lock.release()

    def get(self, key: SSOSessionId) -> Optional[Mapping[str, Any]]:
        """
        Fetch data from cache based on `key'.

        :param key: hash key to use for lookup
        :returns: Any data found matching `key', or None.
        """
        return self._data.get(key)

    def update(self, key: SSOSessionId, info: Any) -> None:
        """
        Update an entry in the cache.

        :param key: Lookup key for entry
        :param info: Value to be stored for 'key'
        :return: None
        """
        self._data[key] = info

    def delete(self, key: SSOSessionId) -> bool:
        """
        Delete an item from the cache.

        :param key: hash key to delete
        :return: True on success
        """
        try:
            del self._data[key]
            return True
        except KeyError:
            logger.debug("Failed deleting key {!r} from {!s} cache (entry did not exist)".format(key, self.name))
        return False

    def items(self) -> Any:
        """
        Return all items from cache.
        """
        return self._data


class SSOSessionCacheError(EduIDDBError):
    pass


class SSOSessionCache(BaseDB):
    def __init__(self, db_uri: str, db_name: str = "eduid_idp", collection: str = "sso_sessions"):
        super().__init__(db_uri, db_name, collection=collection, safe_writes=True)

        # Remove messages older than created_ts + ttl
        indexes = {
            "auto-discard": {"key": [("expires_at", 1)], "expireAfterSeconds": 0},
            "unique-session-id": {"key": [("session_id", 1)], "unique": True},
        }
        self.setup_indexes(indexes)

    def remove_session(self, session: SSOSession) -> bool:
        """
        Remove entries when SLO is executed.
        :return: False on failure
        """
        result = self._coll.delete_one({"_id": session.obj_id})
        logger.debug(f"Removed session {session}: num={result.deleted_count}")
        return bool(result.deleted_count)

    def save(self, session: SSOSession) -> None:
        """
        Add a new SSO session to the cache, or update an existing one.

        The mapping of uid -> user (and data) is used when a user visits another SP before
        the SSO session expires, and the mapping of user -> uid is used if the user requests
        logout (SLO).
        """
        result = self._coll.replace_one({"_id": session.obj_id}, session.to_dict(), upsert=True)
        logger.debug(
            f"Saved SSO session {session} in the db: "
            f"matched={result.matched_count}, modified={result.modified_count}, upserted_id={result.upserted_id}"
        )
        return None

    def get_session(self, sid: SSOSessionId) -> Optional[SSOSession]:
        """
        Lookup an SSO session using the session id (same `sid' previously used with add_session).

        :param sid: Unique session identifier as string
        :param userdb: Database to use to initialise session.idp_user
        :return: The session, if found
        """
        res = self._coll.find_one({"session_id": sid})
        if not res:
            logger.debug(f"No SSO session found with session_id={repr(sid)}")
            return None
        session = SSOSession.from_dict(res)
        return session

    def get_sessions_for_user(self, eppn: str) -> List[SSOSession]:
        """
        Lookup all SSO session ids for a given user. Used in SLO with SOAP binding.

        :param eppn: The eppn to look for

        :return: A list with zero or more SSO sessions
        """
        entrys = self._coll.find({"eppn": eppn})
        res = [SSOSession.from_dict(this) for this in entrys]
        return res
