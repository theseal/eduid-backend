# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 NORDUnet A/S
# Copyright (c) 2019 SUNET
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

import os
import json
from datetime import datetime, timedelta

from mock import patch
import flask.testing

from eduid_common.api.testing import EduidAPITestCase
from eduid_common.config.parsers.etcd import EtcdConfigParser

from eduid_webapp.jsconfig.app import jsconfig_init_app
from eduid_webapp.jsconfig.settings.common import JSConfigConfig
from eduid_webapp.jsconfig.settings.front import FrontConfig


class JSConfigTests(EduidAPITestCase):

    def setUp(self):
        super(JSConfigTests, self).setUp(copy_user_to_private=False)

        self.jsconfig_ns = '/eduid/webapp/jsapps/'
        self.jsconfig_parser = EtcdConfigParser(namespace=self.jsconfig_ns,
                                                host=self.etcd_instance.host,
                                                port=self.etcd_instance.port)

        jsconfig_config = {
            'eduid': {
                'webapp': {
                    'jsapps': {
                        'dashboard_url': 'dummy-url'
                    }
                }
            }
        }
        self.jsconfig_parser.write_configuration(jsconfig_config)
        os.environ['EDUID_CONFIG_NS'] = '/eduid/webapp/jsapps/'
        os.environ['ETCD_HOST'] = self.etcd_instance.host
        os.environ['ETCD_PORT'] = str(self.etcd_instance.port)
        

    def load_app(self, config):
        """
        Called from the parent class, so we can provide the appropriate flask
        app for this test case.
        """
        app = jsconfig_init_app('jsconfig', config)
        app.url_map.host_matching = False
        self.browser = app.test_client(allow_subdomain_redirects=True)
        return app

    def update_config(self, config):
        app_config = {k.lower(): v for k,v in config.items()}
        app_config.update({
            'server_name': 'example.com',
            'tou_url': 'dummy-url',
            'testing': True,
        })
        return JSConfigConfig(**app_config)

    def test_get_dashboard_config(self):
        eppn = self.test_user_data['eduPersonPrincipalName']
        with self.session_cookie(self.browser, eppn) as client:
            response = client.get('http://dashboard.example.com/config')

            self.assertEqual(response.status_code, 200)

            config_data = json.loads(response.data)

            self.assertEqual(config_data['type'], 'GET_JSCONFIG_CONFIG_SUCCESS')
            self.assertEqual(config_data['payload']['dashboard_url'], 'dummy-url')
            self.assertEqual(config_data['payload']['static_faq_url'], '')

    @patch('eduid_webapp.jsconfig.views.requests.get')
    def test_get_signup_config(self, mock_request_get):

        class MockResponse:
            status_code = 200
            headers = {'mock-header': 'dummy-value'}
            def json(self):
                return {
                        'payload': {
                            'test-version-1': '1st Dummy TOU',
                            'test-version-2': '2st Dummy TOU',
                            }
                        }


        mock_request_get.return_value = MockResponse()

        eppn = self.test_user_data['eduPersonPrincipalName']
        with self.session_cookie(self.browser, eppn) as client:
            response = client.get('http://signup.example.com/signup/config')

            self.assertEqual(response.status_code, 200)

            config_data = json.loads(response.data)

            self.assertEqual(config_data['type'], 'GET_JSCONFIG_SIGNUP_CONFIG_SUCCESS')
            self.assertEqual(config_data['payload']['dashboard_url'], 'dummy-url')
            self.assertEqual(config_data['payload']['static_faq_url'], '')
            self.assertEqual(config_data['payload']['tous']['test-version-2'], '2st Dummy TOU')
