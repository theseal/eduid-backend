# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 NORDUnet A/S
# Copyright (c) 2018-2019 SUNET
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
from typing import Any, Dict, Mapping

from eduid.webapp.common.api.testing import EduidAPITestCase
from eduid.webapp.support.app import SupportApp, support_init_app

__author__ = "lundberg"


class SupportAppTests(EduidAPITestCase):
    """Base TestCase for those tests that need a full environment setup"""

    app: SupportApp

    def setUp(self):
        super(SupportAppTests, self).setUp()

        self.test_user_eppn = "hubba-bubba"
        self.client = self.app.test_client()

    def load_app(self, config: Mapping[str, Any]) -> SupportApp:
        """
        Called from the parent class, so we can provide the appropriate flask
        app for this test case.
        """
        return support_init_app("testing", config)

    def update_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        config.update(
            {
                "support_personnel": ["hubba-bubba"],
                "token_service_url_logout": "https://localhost/logout",
                "eduid_static_url": "https://testing.eduid.se/static/",
            }
        )
        return config

    def test_authenticate(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)  # Redirect to token service
        with self.session_cookie(self.client, self.test_user_eppn) as client:
            response = client.get("/")
        self.assertEqual(response.status_code, 200)  # Authenticated request

    def test_search_existing_user(self):
        existing_mail_address = self.test_user.mail_addresses.to_list()[0]
        with self.session_cookie(self.client, self.test_user_eppn) as client:
            response = client.post("/", data={"query": f"{existing_mail_address.email}"})
        assert b'<h3>1 user was found using query "johnsmith@example.com":</h3>' in response.data

    def test_search_non_existing_user(self):
        non_existing_mail_address = "not_in_db@example.com}"
        with self.session_cookie(self.client, self.test_user_eppn) as client:
            response = client.post("/", data={"query": non_existing_mail_address})
        assert b"<h3>No users matched the search query</h3>" in response.data
