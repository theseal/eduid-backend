#!/usr/bin/python
#
# Copyright (c) 2013 NORDUnet A/S
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

import datetime
import logging
from typing import Optional, Tuple

from bson import ObjectId
from mock import patch

import eduid_common.authn
import eduid_userdb
import vccs_client
from eduid_common.api import exceptions
from vccs_client import VCCSClient

from eduid_userdb.idp import IdPUser
from eduid_webapp.idp.idp_authn import AuthnData
from eduid_webapp.idp.tests.test_app import IdPTests

logger = logging.getLogger(__name__)

eduid_common.authn.TESTING = True


class TestIdPUserDb(IdPTests):
    def test_lookup_user_by_email(self):
        _this = self.app.userdb.lookup_user(self.test_user.mail_addresses.primary.email)
        assert _this.eppn == self.test_user.eppn

    def test_lookup_user_by_eppn(self):
        _this = self.app.userdb.lookup_user(self.test_user.eppn)
        assert _this.eppn == self.test_user.eppn

    def test_password_authn(self):
        # Patch the VCCSClient so we do not need a vccs server
        with patch.object(VCCSClient, 'authenticate'):
            VCCSClient.authenticate.return_value = True
            user, res = self._test_authn(self.test_user.mail_addresses.primary.email, 'foo')
            assert user.eppn == self.test_user.eppn
            assert isinstance(res, AuthnData)

    def test_verify_username_and_incorrect_password(self):
        user, authn_data = self._test_authn(self.test_user.mail_addresses.primary.email, 'foo')
        assert user is None
        assert authn_data is None

    def _test_authn(self, username: str, password: str) -> Tuple[Optional[IdPUser], Optional[AuthnData]]:
        data = {
            'username': username,
            'password': password,
        }
        return self.app.authn.password_authn(data)


class TestAuthentication(IdPTests):
    def test_authn_unknown_user(self):
        data = {
            'username': 'foo',
            'password': 'bar',
        }
        user, authn_data = self.app.authn.password_authn(data)
        assert user == None
        self.assertFalse(authn_data)

    @patch('vccs_client.VCCSClient.add_credentials')
    def test_authn_known_user_wrong_password(self, mock_add_credentials):
        mock_add_credentials.return_value = False
        assert isinstance(self.test_user, eduid_userdb.User)
        cred_id = ObjectId()
        factor = vccs_client.VCCSPasswordFactor('foo', str(cred_id), salt=None)
        self.app.authn.auth_client.add_credentials(str(self.test_user.user_id), [factor])
        data = {
            'username': self.test_user.mail_addresses.primary.email,
            'password': 'bar',
        }
        user, authn_data = self.app.authn.password_authn(data)
        assert user is None
        self.assertFalse(authn_data)

    @patch('vccs_client.VCCSClient.authenticate')
    @patch('vccs_client.VCCSClient.add_credentials')
    def test_authn_known_user_right_password(self, mock_add_credentials, mock_authenticate):
        mock_add_credentials.return_value = True
        mock_authenticate.return_value = True
        assert isinstance(self.test_user, eduid_userdb.User)
        passwords = self.test_user.credentials.to_list()
        factor = vccs_client.VCCSPasswordFactor('foo', str(passwords[0].key), salt=passwords[0].salt)
        self.app.authn.auth_client.add_credentials(str(self.test_user.user_id), [factor])
        data = {
            'username': self.test_user.mail_addresses.primary.email,
            'password': 'foo',
        }
        user, authn_data = self.app.authn.password_authn(data)
        assert user is not None
        assert user.eppn == self.test_user.eppn
        assert authn_data is not None

    @patch('vccs_client.VCCSClient.authenticate')
    @patch('vccs_client.VCCSClient.add_credentials')
    def test_authn_expired_credential(self, mock_add_credentials, mock_authenticate):
        mock_add_credentials.return_value = False
        mock_authenticate.return_value = True
        assert isinstance(self.test_user, eduid_userdb.User)
        passwords = self.test_user.credentials.to_list()
        factor = vccs_client.VCCSPasswordFactor('foo', str(passwords[0].key), salt=passwords[0].salt)
        self.app.authn.auth_client.add_credentials(str(self.test_user.user_id), [factor])
        data = {
            'username': self.test_user.mail_addresses.primary.email,
            'password': 'foo',
        }
        # Store a successful authentication using this credential three year ago
        three_years_ago = datetime.datetime.now() - datetime.timedelta(days=3 * 365)
        self.app.authn.authn_store.credential_success([passwords[0].key], three_years_ago)
        with self.assertRaises(exceptions.EduidForbidden):
            self.assertTrue(self.app.authn.password_authn(data))
        # Do the same thing again to make sure we didn't accidentally update the
        # 'last successful login' timestamp when it was a successful login with an
        # expired credential.
        with self.assertRaises(exceptions.EduidForbidden):
            self.assertTrue(self.app.authn.password_authn(data))
