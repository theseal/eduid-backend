#
# Copyright (c) 2014-2015 NORDUnet A/S
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

import copy
import datetime
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

import bson

from eduid_userdb.credentials import CredentialList
from eduid_userdb.element import UserDBValueError
from eduid_userdb.exceptions import UserHasNotCompletedSignup, UserHasUnknownData, UserIsRevoked, UserMissingData
from eduid_userdb.locked_identity import LockedIdentityList
from eduid_userdb.mail import MailAddressList
from eduid_userdb.nin import NinList
from eduid_userdb.orcid import Orcid
from eduid_userdb.phone import PhoneNumberList
from eduid_userdb.profile import ProfileList
from eduid_userdb.tou import ToUList

VALID_SUBJECT_VALUES = ['physical person']

TUserSubclass = TypeVar('TUserSubclass', bound='User')


@dataclass
class User(object):
    """
    Generic eduID user object.
    """
    user_id: bson.ObjectId
    eppn: Optional[str] = None
    given_name: str = ''
    display_name: str = ''
    surname: str = ''
    subject: Optional[str] = None
    language: str = 'sv'
    mail_addresses: MailAddressList = field(default_factory=MailAddressList)
    phone_numbers: PhoneNumberList = field(default_factory=PhoneNumberList)
    credentials: CredentialList = field(default_factory=CredentialList)
    nins: NinList = field(default_factory=NinList)
    modified_ts: datetime.datetime = field(default_factory=datetime.utcnow)
    entitlements: List[str] = field(default_factory=list)
    tou: ToUList = field(default_factory=ToUList)
    terminated: datetime.datetime = field(default_factory=datetime.utcnow)
    locked_identity: LockedIdentityList = field(default_factory=LockedIdentityList)
    orcid: Optional[Orcid] = None
    profiles: ProfileList = field(default_factory=ProfileList)

    @classmethod
    def construct_user(
        cls: Type[TUserSubclass],
        eppn: Optional[str] = None,
        _id: Optional[Union[bson.ObjectId, str]] = None,
        subject: Optional[str] = None,
        display_name: Optional[str] = None,
        given_name: Optional[str] = None,
        surname: Optional[str] = None,
        language: Optional[str] = None,
        passwords: Optional[CredentialList] = None,
        modified_ts: Optional[datetime.datetime] = None,
        revoked_ts: Optional[datetime.datetime] = None,
        entitlements: Optional[List[str]] = None,
        terminated: Optional[bool] = None,
        letter_proofing_data: Optional[dict] = None,
        mail_addresses: Optional[MailAddressList] = None,
        phone_numbers: Optional[PhoneNumberList] = None,
        nins: Optional[NinList] = None,
        tou: Optional[ToUList] = None,
        locked_identity: Optional[LockedIdentityList] = None,
        orcid: Optional[Orcid] = None,
        profiles: Optional[ProfileList] = None,
        raise_on_unknown: bool = True,
        **kwargs,
    ) -> TUserSubclass:
        """
        Construct user from data in typed params.
        """

        data: Dict[str, Any] = {}

        data['_id'] = _id
        if eppn is None:
            raise UserMissingData("User objects must be constructed with an eppn")
        data['eduPersonPrincipalName'] = eppn
        data['subject'] = subject
        data['displayName'] = display_name
        data['givenName'] = given_name
        data['surname'] = surname
        data['preferredLanguage'] = language
        data['modified_ts'] = modified_ts
        data['terminated'] = terminated
        if revoked_ts is not None:
            data['revoked_ts'] = revoked_ts
        if orcid is not None:
            data['orcid'] = orcid.to_dict()
        if letter_proofing_data is not None:
            data['letter_proofing_data'] = letter_proofing_data
        if passwords is not None:
            data['passwords'] = passwords.to_list_of_dicts()
        if entitlements is not None:
            data['entitlements'] = entitlements
        if mail_addresses is not None:
            data['mailAliases'] = mail_addresses.to_list_of_dicts()
        if phone_numbers is not None:
            data['phone'] = phone_numbers.to_list_of_dicts()
        if nins is not None:
            data['nins'] = nins.to_list_of_dicts()
        if tou is not None:
            data['tou'] = tou.to_list_of_dicts()
        if locked_identity is not None:
            data['locked_identity'] = locked_identity.to_list_of_dicts()
        if profiles is not None:
            data['profiles'] = profiles.to_list_of_dicts()

        data.update(kwargs)

        return cls.from_dict(data)

    def check_or_use_data(self):
        """
        Derived classes can override this method to check that the provided data
        is enough for their purposes, or to deal specially with particular bits of it.

        In case of problems they sould raise whatever Exception is appropriate.
        """
        pass

    @classmethod
    def from_dict(cls: Type[TUserSubclass], data: Dict[str, Any], raise_on_unknown: bool = True) -> TUserSubclass:
        """
        Construct user from a data dict.
        """
        self = object.__new__(cls)

        self._data_in = copy.deepcopy(data)  # to not modify callers data
        self._data_orig = copy.deepcopy(data)  # to not modify callers data
        self._data: Dict[str, Any] = dict()

        self.check_or_use_data()

        self._parse_check_invalid_users()

        # things without setters
        _id = self._data_in.pop('_id', None)
        if _id is None:
            _id = bson.ObjectId()
        if not isinstance(_id, bson.ObjectId):
            _id = bson.ObjectId(_id)
        self._data['_id'] = _id

        if 'sn' in self._data_in:
            _sn = self._data_in.pop('sn')
            # Some users have both 'sn' and 'surname'. In that case, assume sn was
            # once converted to surname but also left behind, and discard 'sn'.
            if 'surname' not in self._data_in:
                self._data_in['surname'] = _sn
        if 'eduPersonEntitlement' in self._data_in:
            self._data_in['entitlements'] = self._data_in.pop('eduPersonEntitlement')

        self._parse_mail_addresses()
        self._parse_phone_numbers()
        self._parse_nins()
        self._parse_tous()
        self._parse_locked_identity()
        self._parse_orcid()
        self._parse_profiles()

        self._credentials = CredentialList(self._data_in.pop('passwords', []))
        # generic (known) attributes
        self.eppn = self._data_in.pop('eduPersonPrincipalName')  # mandatory
        self.subject = self._data_in.pop('subject', None)
        self.display_name = self._data_in.pop('displayName', None)
        self.given_name = self._data_in.pop('givenName', None)
        self.surname = self._data_in.pop('surname', None)
        self.language = self._data_in.pop('preferredLanguage', None)
        self.modified_ts = self._data_in.pop('modified_ts', None)
        self.entitlements = self._data_in.pop('entitlements', None)
        self.terminated = self._data_in.pop('terminated', None)
        # obsolete attributes
        if 'postalAddress' in self._data_in:
            del self._data_in['postalAddress']
        if 'date' in self._data_in:
            del self._data_in['date']
        if 'csrf' in self._data_in:
            del self._data_in['csrf']
        # temporary data we just want to retain as is
        for copy_attribute in ['letter_proofing_data']:
            if copy_attribute in self._data_in:
                self._data[copy_attribute] = self._data_in.pop(copy_attribute)

        if len(self._data_in) > 0:
            if raise_on_unknown:
                raise UserHasUnknownData(
                    'User {!s}/{!s} unknown data: {!r}'.format(self.user_id, self.eppn, self._data_in.keys())
                )
            # Just keep everything that is left as-is
            self._data.update(self._data_in)

        return self

    def __repr__(self):
        return '<eduID {!s}: {!s}/{!s}>'.format(self.__class__.__name__, self.eppn, self.user_id,)

    def __eq__(self, other):
        if self.__class__ is not other.__class__:
            raise TypeError(
                'Trying to compare objects of different class {!r} - {!r} '.format(self.__class__, other.__class__)
            )
        return self._data == other._data

    def _parse_check_invalid_users(self):
        """
        Part of __init__().

        Check users that can't be loaded for some known reason.
        """
        if 'revoked_ts' in self._data_in:
            raise UserIsRevoked(
                'User {!s}/{!s} was revoked at {!s}'.format(
                    self._data_in.get('_id'), self._data_in.get('eduPersonPrincipalName'), self._data_in['revoked_ts']
                )
            )
        if 'passwords' not in self._data_in:
            raise UserHasNotCompletedSignup(
                'User {!s}/{!s} is incomplete'.format(
                    self._data_in.get('_id'), self._data_in.get('eduPersonPrincipalName')
                )
            )

    def _parse_mail_addresses(self):
        """
        Part of __init__().

        Parse all the different formats of mail+mailAliases attributes in the database.
        """
        _mail_addresses = self._data_in.pop('mailAliases', [])
        if 'mail' in self._data_in:
            # old-style userdb primary e-mail address indicator
            for idx in range(len(_mail_addresses)):
                if _mail_addresses[idx]['email'] == self._data_in['mail']:
                    if 'passwords' in self._data_in:
                        # Work around a bug where one could signup, not follow the link in the e-mail
                        # and then do a password reset to set a password. The e-mail address is
                        # implicitly verified by the password reset (which must have been done using e-mail).
                        _mail_addresses[idx]['verified'] = True
                    # If a user does not already have a primary mail address promote "mail" to primary if
                    # it is verified
                    _has_primary = any([item.get('primary', False) for item in _mail_addresses])
                    if _mail_addresses[idx].get('verified', False) and not _has_primary:
                        _mail_addresses[idx]['primary'] = True
            self._data_in.pop('mail')

        if len(_mail_addresses) == 1 and _mail_addresses[0].get('verified', False):
            if not _mail_addresses[0].get('primary', False):
                # A single mail address was not set as Primary until it was verified
                _mail_addresses[0]['primary'] = True

        self._mail_addresses = MailAddressList(_mail_addresses)

    def _parse_phone_numbers(self):
        """
        Part of __init__().

        Parse all the different formats of mobile/phone attributes in the database.
        """
        if 'mobile' in self._data_in:
            _mobile = self._data_in.pop('mobile')
            if 'phone' not in self._data_in:
                # Some users have both 'mobile' and 'phone'. Assume mobile was once transformed
                # to 'phone' but also left behind - so just discard 'mobile'.
                self._data_in['phone'] = _mobile
        if 'phone' in self._data_in:
            _phones = self._data_in.pop('phone')
            # Clean up for non verified phone elements that where still primary
            for _this in _phones:
                if not _this.get('verified', False) and _this.get('primary', False):
                    _this['primary'] = False
            _primary = [x for x in _phones if x.get('primary', False)]
            if _phones and not _primary:
                # None of the phone numbers are primary. Promote the first verified
                # entry found (or none if there are no verified entries).
                for _this in _phones:
                    if _this.get('verified', False):
                        _this['primary'] = True
                        break
            self._data_in['phone'] = _phones

        _phones = self._data_in.pop('phone', [])

        self._phone_numbers = PhoneNumberList(_phones)

    def _parse_nins(self):
        """
        Part of __init__().

        Parse all the different formats of norEduPersonNIN attributes in the database.
        """
        _nins = self._data_in.pop('nins', [])
        if 'norEduPersonNIN' in self._data_in:
            # old-style list of verified nins
            old_nins = self._data_in.pop('norEduPersonNIN')
            for this in old_nins:
                if isinstance(this, str):
                    # XXX lookup NIN in eduid-dashboards verifications to make sure it is verified somehow?
                    _primary = not _nins
                    _nins.append(
                        {'number': this, 'primary': _primary, 'verified': True,}
                    )
                elif isinstance(this, dict):
                    _nins.append(
                        {
                            'number': this.pop('number'),
                            'primary': this.pop('primary'),
                            'verified': this.pop('verified'),
                        }
                    )
                    if len(this):
                        raise UserDBValueError('Old-style NIN-as-dict has unknown data')
                else:
                    raise UserDBValueError('Old-style NIN is not a string or dict')
        self._nins = NinList(_nins)

    def _parse_tous(self):
        """
        Part of __init__().

        Parse the ToU acceptance events.
        """
        _tou = self._data_in.pop('tou', [])
        self._tou = ToUList(_tou)

    def _parse_locked_identity(self):
        """
        Part of __init__().

        Parse the LockedIdentity elements.
        """
        _locked_identity = self._data_in.pop('locked_identity', [])
        self._locked_identity = LockedIdentityList(_locked_identity)

    def _parse_orcid(self):
        """
        Part of __init__().

        Parse the Orcid element.
        """
        self._orcid = None
        _orcid = self._data_in.pop('orcid', None)
        if _orcid is not None:
            self._orcid = Orcid.from_dict(_orcid)

    def _parse_profiles(self):
        """
        Part of __init__().

        Parse the Profile elements.
        """
        _profiles = self._data_in.pop('profiles', [])
        self._profiles = ProfileList.from_list_of_dicts(_profiles)

    def to_dict(self, old_userdb_format=False):
        """
        Return user data serialized into a dict that can be stored in MongoDB.

        :param old_userdb_format: Set to True to get the dict in the old database format.
        :type old_userdb_format: bool

        :return: User as dict
        :rtype: dict
        """
        res = copy.copy(asdict(self._data))  # avoid caller messing up our private _data
        res['mailAliases'] = self.mail_addresses.to_list_of_dicts(old_userdb_format=old_userdb_format)
        res['phone'] = self.phone_numbers.to_list_of_dicts(old_userdb_format=old_userdb_format)
        res['passwords'] = self.credentials.to_list_of_dicts(old_userdb_format=old_userdb_format)
        res['nins'] = self.nins.to_list_of_dicts(old_userdb_format=old_userdb_format)
        res['tou'] = self.tou.to_list_of_dicts()
        res['locked_identity'] = self.locked_identity.to_list_of_dicts(old_userdb_format=old_userdb_format)
        res['orcid'] = None
        if self.orcid is not None:
            res['orcid'] = self.orcid.to_dict()
        if 'eduPersonEntitlement' not in res:
            res['eduPersonEntitlement'] = res.pop('entitlements', [])
        # Remove these values if they have a value that evaluates to False
        for _remove in [
            'displayName',
            'givenName',
            'surname',
            'preferredLanguage',
            'phone',
            'orcid',
            'eduPersonEntitlement',
            'locked_identity',
            'nins',
        ]:
            if _remove in res and not res[_remove]:
                del res[_remove]
        if old_userdb_format:
            _primary = self.mail_addresses.primary
            if _primary:
                res['mail'] = _primary.email
            if 'phone' in res:
                res['mobile'] = res.pop('phone')
            if 'surname' in res:
                res['sn'] = res.pop('surname')
            if 'nins' in res:
                # Extract all verified NINs and return as a list of strings
                _nins = res.pop('nins')
                verified_nins = [this['number'] for this in _nins if this['verified']]
                # don't even put 'norEduPersonNIN' in res if it is empty
                if verified_nins:
                    res['norEduPersonNIN'] = verified_nins
                elif 'norEduPersonNIN' in res:
                    del res['norEduPersonNIN']
            if res.get('mailAliases') is list():
                del res['mailAliases']
        return res

    # -----------------------------------------------------------------
    @classmethod
    def from_user(cls, user, private_userdb):
        """
        This function is only expected to be used by subclasses of User.

        :param user: User instance from AM database
        :param private_userdb: Private UserDB to load modified_ts from

        :type user: User
        :type private_userdb: eduid_userdb.UserDB

        :return: User proper
        :rtype: cls
        """
        user_dict = user.to_dict()
        private_user = private_userdb.get_user_by_eppn(user.eppn, raise_on_missing=False)
        if private_user is None:
            user_dict.pop('modified_ts', None)
        else:
            user_dict['modified_ts'] = private_user.modified_ts
        return cls.from_dict(data=user_dict)
