# -*- coding: utf-8 -*-
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
# Author : Johan Lundberg <lundberg@nordu.net>
#
import copy

from bson.objectid import ObjectId
from six import string_types

from eduid_userdb.element import Element
from eduid_userdb.exceptions import UserHasUnknownData, UserDBValueError

__author__ = 'lundberg'


class Password(Element):

    def __init__(self, credential_id=None, salt=None, application=None, created_ts=None, data=None,
                 raise_on_unknown=True):
        data_in = data
        data = copy.copy(data_in)  # to not modify callers data

        if data is None:
            if created_ts is None:
                created_ts = True
            data = dict(id = credential_id,
                        salt = salt,
                        created_by = application,
                        created_ts = created_ts,
                        )

        if 'source' in data:  # XXX Load and save all users in the database to replace source with created_by
            data['created_by'] = data.pop('source')
        Element.__init__(self, data)
        self.id = data.pop('id')
        self.salt = data.pop('salt')

        leftovers = data.keys()
        if leftovers:
            if raise_on_unknown:
                raise UserHasUnknownData('Password {!r} unknown data: {!r}'.format(
                    self.id, leftovers,
                ))
            # Just keep everything that is left as-is
            self._data.update(data)

    @property
    def key(self):
        """
        Return the element that is used as key.
        """
        return self.id

    @property
    def id(self):
        """
        This is a reference to the ObjectId in the authentication private database.

        :return: Unique ID of password.
        :rtype: bson.ObjectId
        """
        return self._data['id']

    @id.setter
    def id(self, value):
        """
        :param value: Unique ID of password.
        :type value: bson.ObjectId
        """
        if not isinstance(value, ObjectId):
            raise UserDBValueError("Invalid 'id': {!r}".format(value))
        self._data['id'] = value

    @property
    def salt(self):
        """
        This is a reference to the ObjectId in the authentication private database.

        :return: Password salt.
        :rtype: str
        """
        return self._data['salt']

    @salt.setter
    def salt(self, value):
        """
        :param value: Password salt.
        :type value: str
        """
        if not isinstance(value, string_types):
            raise UserDBValueError("Invalid 'salt': {!r}".format(value))
        self._data['salt'] = value

    def to_dict(self, old_userdb_format=False):
        if not old_userdb_format:
            return self._data
        old = copy.copy(self._data)
        return old


def password_from_dict(data, raise_on_unknown=True):
    """
    Create a Password instance from a dict.

    :param data: Password parameters from database
    :param raise_on_unknown: Raise UserHasUnknownData if unrecognized data is encountered

    :type data: dict
    :type raise_on_unknown: bool
    :rtype: Password
    """
    return Password(data=data, raise_on_unknown=raise_on_unknown)