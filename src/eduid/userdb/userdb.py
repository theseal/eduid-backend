#
# Copyright (c) 2015 NORDUnet A/S
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
import logging
from abc import ABC
from typing import Any, Generic, List, Mapping, Optional, TypeVar, Union

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument

import eduid.userdb.exceptions
from eduid.userdb.db import BaseDB
from eduid.userdb.exceptions import DocumentDoesNotExist, EduIDUserDBError, MultipleUsersReturned, UserDoesNotExist
from eduid.userdb.user import User
from eduid.userdb.util import utc_now

logger = logging.getLogger(__name__)

UserVar = TypeVar('UserVar')


class UserDB(BaseDB, Generic[UserVar], ABC):
    """
    Interface class to the central eduID UserDB.

    :param db_uri: mongodb:// URI to connect to
    :param db_name: mongodb database name
    :param collection: mongodb collection name
    """

    def __init__(self, db_uri: str, db_name: str, collection: str = 'userdb'):

        if db_name == 'eduid_am' and collection == 'userdb':
            # Hack to get right collection name while the configuration points to the old database
            collection = 'attributes'
        self.collection = collection

        super().__init__(db_uri, db_name, collection)

        logger.debug(f'{self} connected to database')
        # XXX Backwards compatibility.
        # Was: provide access to our backends exceptions to users of this class
        self.exceptions = eduid.userdb.exceptions

    def __repr__(self):
        return f'<eduID {self.__class__.__name__}: {self._db.sanitized_uri} {repr(self._coll_name)})>'

    __str__ = __repr__

    @classmethod
    def user_from_dict(cls, data):
        # must be implemented by subclass to get correct type information
        raise NotImplementedError(f'user_from_dict not implemented in UserDB subclass {cls}')

    def get_user_by_id(self, user_id: Union[str, ObjectId]) -> Optional[UserVar]:
        """
        Locate a user in the userdb given the user's _id.

        :param user_id: User identifier

        :return: User instance | None
        """
        if not isinstance(user_id, ObjectId):
            try:
                user_id = ObjectId(user_id)
            except InvalidId:
                return None
        return self._get_user_by_attr('_id', user_id)

    def _get_user_by_filter(self, filter: Mapping[str, Any]) -> List[UserVar]:
        """
        return the user matching the provided filter.

        :param filter: The filter to match the user

        :return: List of User instances
        """
        try:
            users = list(self._get_documents_by_filter(filter))
        except DocumentDoesNotExist:
            logger.debug("{!s} No user found with filter {!r} in {!r}".format(self, filter, self._coll_name))
            raise UserDoesNotExist("No user matching filter {!r}".format(filter))

        return [self.user_from_dict(data=user) for user in users]

    def get_user_by_mail(self, email: str) -> Optional[UserVar]:
        """ Locate a user with a (confirmed) e-mail address """
        res = self.get_users_by_mail(email=email)
        if not res:
            return None
        if len(res) > 1:
            raise MultipleUsersReturned(f'Multiple matching users for email {repr(email)}')
        return res[0]

    def get_users_by_mail(self, email: str, include_unconfirmed: bool = False) -> List[UserVar]:
        """
        Return the user object in the central eduID UserDB having
        an email address matching `email'. Unless include_unconfirmed=True, the
        email address has to be confirmed/verified.

        :param email: The email address to look for
        :param include_unconfirmed: Require email address to be confirmed/verified.

        :return: User instance
        """
        email = email.lower()
        elemmatch = {'email': email, 'verified': True}
        if include_unconfirmed:
            elemmatch = {'email': email}
        filter = {'$or': [{'mail': email}, {'mailAliases': {'$elemMatch': elemmatch}}]}
        return self._get_user_by_filter(filter)

    def get_user_by_nin(self, nin: str) -> Optional[UserVar]:
        """ Locate a user with a (confirmed) NIN """
        res = self.get_users_by_nin(nin=nin)
        if not res:
            return None
        if len(res) > 1:
            raise MultipleUsersReturned(f'Multiple matching users for NIN {repr(nin)}')
        return res[0]

    def get_users_by_nin(self, nin: str, include_unconfirmed: bool = False) -> List[UserVar]:
        """
        Return the user object in the central eduID UserDB having
        a NIN matching `nin'. Unless include_unconfirmed=True, the
        NIN has to be confirmed/verified.

        :param nin: The nin to look for
        :param include_unconfirmed: Require nin to be confirmed/verified.

        :return: List of User instances
        """
        old_filter = {'norEduPersonNIN': nin}
        newmatch = {'number': nin, 'verified': True}
        if include_unconfirmed:
            newmatch = {'number': nin}
        new_filter = {'nins': {'$elemMatch': newmatch}}
        filter = {'$or': [old_filter, new_filter]}
        return self._get_user_by_filter(filter)

    def get_user_by_phone(self, phone: str) -> Optional[UserVar]:
        """ Locate a user with a (confirmed) phone number """
        res = self.get_users_by_phone(phone=phone)
        if not res:
            return None
        if len(res) > 1:
            raise MultipleUsersReturned(f'Multiple matching users for phone {repr(phone)}')
        return res[0]

    def get_users_by_phone(self, phone: str, include_unconfirmed: bool = False) -> List[UserVar]:
        """
        Return the user object in the central eduID UserDB having
        a phone number matching `phone'. Unless include_unconfirmed=True, the
        phone number has to be confirmed/verified.

        :param phone: The phone to look for
        :param include_unconfirmed: Require phone to be confirmed/verified.

        :return: List of User instances
        """
        oldmatch = {'mobile': phone, 'verified': True}
        if include_unconfirmed:
            oldmatch = {'mobile': phone}
        old_filter = {'mobile': {'$elemMatch': oldmatch}}
        newmatch = {'number': phone, 'verified': True}
        if include_unconfirmed:
            newmatch = {'number': phone}
        new_filter = {'phone': {'$elemMatch': newmatch}}
        filter = {'$or': [old_filter, new_filter]}
        return self._get_user_by_filter(filter)

    def get_user_by_eppn(self, eppn: Optional[str]) -> Optional[UserVar]:
        """
        Look for a user using the eduPersonPrincipalName.

        :param eppn: eduPersonPrincipalName to look for
        """
        # allow eppn=None as convenience, to not have to check it everywhere before calling this function
        if eppn is None:
            return None
        return self._get_user_by_attr('eduPersonPrincipalName', eppn)

    def _get_user_by_attr(self, attr: str, value: Any) -> Optional[UserVar]:
        """
        Locate a user in the userdb using any attribute and value.

        This is a private function since callers can't depend on the name of things in the db.

        :param attr: The attribute to match on
        :param value: The value to match on

        :raise self.UserDoesNotExist: No user match the search criteria
        :raise self.MultipleUsersReturned: More than one user matches the search criteria
        """
        user = None
        logger.debug("{!s} Looking in {!r} for user with {!r} = {!r}".format(self, self._coll_name, attr, value))
        try:
            doc = self._get_document_by_attr(attr, value)
            if doc is not None:
                logger.debug("{!s} Found user with id {!s}".format(self, doc['_id']))
                user = self.user_from_dict(data=doc)
                logger.debug("{!s} Returning user {!s}".format(self, user))
            return user
        except self.exceptions.DocumentDoesNotExist as e:
            logger.debug("UserDoesNotExist, {!r} = {!r}".format(attr, value))
            raise UserDoesNotExist(e.reason)
        except self.exceptions.MultipleDocumentsReturned as e:
            logger.error("MultipleUsersReturned, {!r} = {!r}".format(attr, value))
            raise MultipleUsersReturned(e.reason)

    def save(self, user: UserVar, check_sync: bool = True) -> bool:
        """
        :param user: User object
        :param check_sync: Ensure the user hasn't been updated in the database since it was loaded
        """
        if not isinstance(user, User):
            raise EduIDUserDBError(f'user is not a subclass of User')

        if not isinstance(user.user_id, ObjectId):
            raise AssertionError(f'user.user_id is not of type {ObjectId}')

        # XXX add modified_by info. modified_ts alone is not unique when propagated to eduid.workers.am.

        modified = user.modified_ts
        user.modified_ts = utc_now()
        if modified is None:
            # profile has never been modified through the dashboard.
            # possibly just created in signup.
            result = self._coll.replace_one({'_id': user.user_id}, user.to_dict(), upsert=True)
            logger.debug(f'{self} Inserted new user {user} into {self._coll_name}: {repr(result)})')
            import pprint

            extra_debug = pprint.pformat(user.to_dict(), width=120)
            logger.debug(f"Extra debug:\n{extra_debug}")
        else:
            test_doc = {'_id': user.user_id}
            if check_sync:
                test_doc['modified_ts'] = modified
            result = self._coll.replace_one(test_doc, user.to_dict(), upsert=(not check_sync))
            if check_sync and result.modified_count == 0:
                db_ts = None
                db_user = self._coll.find_one({'_id': user.user_id})
                if db_user:
                    db_ts = db_user['modified_ts']
                logger.debug(
                    f'{self} FAILED Updating user {user} (ts {modified}) in {self._coll_name}, ts in db = {db_ts}'
                )
                raise eduid.userdb.exceptions.UserOutOfSync('Stale user object can\'t be saved')
            logger.debug(f"{self} Updated user {user} (ts {modified}) in {self._coll_name}: {result}")
            import pprint

            extra_debug = pprint.pformat(user.to_dict(), width=120)
            logger.debug(f"Extra debug:\n{extra_debug}")
        return result.acknowledged

    def remove_user_by_id(self, user_id: ObjectId) -> bool:
        """
        Remove a user in the userdb given the user's _id.

        NOTE: Full removal of a user should never be done in the central userdb. Kantara
        requires guarantees to not re-use user identifiers (eppn and _id in eduid) and
        we implement that by never removing the complete document from the central userdb.

        Some other applications might have legitimate reasons to remove users from their
        private userdb collections though (like eduid-signup, at the end of the signup
        process).

        This method should ideally then only be available on eduid_signup.userdb.SignupUserDB
        objects, but then eduid-am would have to depend on eduid_signup... Maybe the cleanup
        could be done by the Signup application itself though.

        :param user_id: User id
        """
        logger.debug("{!s} Removing user with id {!r} from {!r}".format(self, user_id, self._coll_name))
        return self.remove_document(spec_or_id=user_id)

    def update_user(self, obj_id: ObjectId, operations: Mapping) -> None:
        """
        Update (or insert) a user document in mongodb.

        operations must be a dict with update operators ({'$set': ..., '$unset': ...}).
        https://docs.mongodb.com/manual/reference/operator/update/

        This update method should only be used in the eduid Attribute Manager when
        merging updates from applications into the central eduID userdb.
        """
        logger.debug(f'{self} updating user {obj_id} in {repr(self._coll_name)} with operations:\n{operations}')

        query_filter = {'_id': obj_id}

        # Check that the operations dict includes only the whitelisted operations
        whitelisted_operations = ['$set', '$unset']
        bad_operators = [key for key in operations if key not in whitelisted_operations]
        if bad_operators:
            logger.debug(f'Tried to update/insert document: {query_filter} with operations: {operations}')
            error_msg = f'Invalid update operator: {bad_operators}'
            logger.error(error_msg)
            raise eduid.userdb.exceptions.EduIDDBError(error_msg)

        updated_doc = self._coll.find_one_and_update(
            filter=query_filter, update=operations, return_document=ReturnDocument.AFTER, upsert=True
        )
        logger.debug(f'Updated/inserted document: {updated_doc}')


class AmDB(UserDB[User]):
    """ Central userdb, aka. AM DB """

    def __init__(self, db_uri: str, db_name: str = 'eduid_am'):
        super().__init__(db_uri, db_name)

    @classmethod
    def user_from_dict(cls, data: Mapping[str, Any]) -> User:
        return User.from_dict(data)
