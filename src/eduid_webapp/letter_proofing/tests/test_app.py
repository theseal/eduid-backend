# -*- coding: utf-8 -*-

from __future__ import absolute_import

import json
from collections import OrderedDict
from datetime import datetime
from typing import Any, Dict, Optional

from mock import Mock, patch

from eduid_common.api.testing import EduidAPITestCase
from eduid_userdb.locked_identity import LockedIdentityNin
from eduid_userdb.nin import Nin

from eduid_webapp.letter_proofing.app import init_letter_proofing_app
from eduid_webapp.letter_proofing.helpers import LetterMsg
from eduid_webapp.letter_proofing.settings.common import LetterProofingConfig

__author__ = 'lundberg'


class LetterProofingTests(EduidAPITestCase):
    """Base TestCase for those tests that need a full environment setup"""

    def setUp(self):
        self.test_user_eppn = 'hubba-baar'
        self.test_user_nin = '200001023456'
        self.test_user_wrong_nin = '190001021234'
        self.mock_address = OrderedDict(
            [
                (
                    u'Name',
                    OrderedDict(
                        [(u'GivenNameMarking', u'20'), (u'GivenName', u'Testaren Test'), (u'Surname', u'Testsson')]
                    ),
                ),
                (
                    u'OfficialAddress',
                    OrderedDict(
                        [(u'Address2', u'\xd6RGATAN 79 LGH 10'), (u'PostalCode', u'12345'), (u'City', u'LANDET')]
                    ),
                ),
            ]
        )
        super(LetterProofingTests, self).setUp(users=['hubba-baar'])

    @staticmethod
    def mock_response(status_code=200, content=None, json_data=None, headers=dict(), raise_for_status=None):
        """
        since we typically test a bunch of different
        requests calls for a service, we are going to do
        a lot of mock responses, so its usually a good idea
        to have a helper function that builds these things
        """
        mock_resp = Mock()
        # mock raise_for_status call w/optional error
        mock_resp.raise_for_status = Mock()
        if raise_for_status:
            mock_resp.raise_for_status.side_effect = raise_for_status
        # set status code and content
        mock_resp.status_code = status_code
        mock_resp.content = content
        # set headers
        mock_resp.headers = headers
        # add json data if provided
        if json_data:
            mock_resp.json = Mock(return_value=json_data)
        return mock_resp

    def load_app(self, config):
        """
        Called from the parent class, so we can provide the appropriate flask
        app for this test case.
        """
        return init_letter_proofing_app('testing', config)

    def update_config(self, app_config):
        app_config.update(
            {
                # 'ekopost_debug_pdf': devnull,
                'ekopost_api_uri': 'http://localhost',
                'ekopost_api_user': 'ekopost_user',
                'ekopost_api_pw': 'secret',
                'letter_wait_time_hours': 336,
                'msg_broker_url': 'amqp://dummy',
                'am_broker_url': 'amqp://dummy',
                'celery_config': {
                    'result_backend': 'amqp',
                    'task_serializer': 'json',
                    'mongo_uri': app_config['mongo_uri'],
                },
            }
        )
        return LetterProofingConfig(**app_config)

    # Helper methods
    def get_state(self):
        with self.session_cookie(self.browser, self.test_user_eppn) as client:
            response = client.get('/proofing')
        self.assertEqual(response.status_code, 200)
        return json.loads(response.data)

    def send_letter(self, nin: str, csrf_token: str) -> Dict[str, Any]:
        """
        Invoke the POST /proofing endpoint, check that the HTTP response code is 200 and return the JSON data.
        """
        response = self.send_letter2(nin, csrf_token)
        self.assertEqual(response.status_code, 200)
        return json.loads(response.data)

    @patch('hammock.Hammock._request')
    @patch('eduid_common.api.am.AmRelay.request_user_sync')
    @patch('eduid_common.api.msg.MsgRelay.get_postal_address')
    def send_letter2(self, nin: str, csrf_token: str, mock_get_postal_address, mock_request_user_sync, mock_hammock):
        """
        Invoke the POST /proofing endpoint and return the whole response.

        To be used with the data validation functions _check_success_response and _check_error_response.
        """
        ekopost_response = self.mock_response(json_data={'id': 'test'})
        mock_hammock.return_value = ekopost_response
        mock_request_user_sync.side_effect = self.request_user_sync
        mock_get_postal_address.return_value = self.mock_address
        data = {'nin': nin, 'csrf_token': csrf_token}
        with self.session_cookie(self.browser, self.test_user_eppn) as client:
            response = client.post('/proofing', data=json.dumps(data), content_type=self.content_type_json)
        return response

    def verify_code(self, code: str, csrf_token: str) -> Dict[str, Any]:
        """
        Invoke the POST /verify-code endpoint, check that the HTTP response code is 200 and return the JSON data.
        """
        response = self.verify_code2(code, csrf_token)
        self.assertEqual(response.status_code, 200)
        return json.loads(response.data)

    @patch('eduid_common.api.am.AmRelay.request_user_sync')
    @patch('eduid_common.api.msg.MsgRelay.get_postal_address')
    def verify_code2(self, code: str, csrf_token: str, mock_get_postal_address, mock_request_user_sync):
        """
        Invoke the POST /verify-code endpoint and return the whole response.

        To be used with the data validation functions _check_success_response and _check_error_response.
        """
        mock_request_user_sync.side_effect = self.request_user_sync
        mock_get_postal_address.return_value = self.mock_address
        data = {'code': code, 'csrf_token': csrf_token}
        with self.session_cookie(self.browser, self.test_user_eppn) as client:
            response = client.post('/verify-code', data=json.dumps(data), content_type=self.content_type_json)
        return response

    @patch('hammock.Hammock._request')
    @patch('eduid_common.api.am.AmRelay.request_user_sync')
    @patch('eduid_common.api.msg.MsgRelay.get_postal_address')
    def get_code_backdoor(
        self,
        mock_get_postal_address: Any,
        mock_request_user_sync: Any,
        mock_hammock: Any,
        cookie_value: Optional[str] = None,
        add_cookie: bool = True,
    ):
        ekopost_response = self.mock_response(json_data={'id': 'test'})
        mock_hammock.return_value = ekopost_response
        mock_request_user_sync.side_effect = self.request_user_sync
        mock_get_postal_address.return_value = self.mock_address

        nin = self.test_user_nin
        json_data = self.get_state()
        csrf_token = json_data['payload']['csrf_token']
        data = {'nin': nin, 'csrf_token': csrf_token}

        with self.session_cookie(self.browser, self.test_user_eppn) as client:
            response = client.post('/proofing', data=json.dumps(data), content_type=self.content_type_json)
            self.assertEqual(response.status_code, 200)

            if cookie_value is None:
                cookie_value = self.app.config.magic_cookie

            if add_cookie:
                client.set_cookie('localhost', key=self.app.config.magic_cookie_name, value=cookie_value)

            return client.get('/get-code')

    # End helper methods

    def test_authenticate(self):
        response = self.browser.get('/proofing')
        self.assertEqual(response.status_code, 302)  # Redirect to token service
        with self.session_cookie(self.browser, self.test_user_eppn) as client:
            response = client.get('/proofing')
        self.assertEqual(response.status_code, 200)  # Authenticated request

    def test_letter_not_sent_status(self):
        json_data = self.get_state()
        assert json_data['payload']['message'] == LetterMsg.no_state.value

    def test_send_letter(self):
        json_data = self.get_state()
        csrf_token = json_data['payload']['csrf_token']
        response = self.send_letter2(self.test_user_nin, csrf_token)
        self._check_success_response(response, type_='POST_LETTER_PROOFING_PROOFING_SUCCESS', msg=LetterMsg.letter_sent)
        expires = response.json['payload']['letter_expires']
        expires = datetime.utcfromtimestamp(int(expires))
        self.assertIsInstance(expires, datetime)
        expires = expires.strftime('%Y-%m-%d')
        self.assertIsInstance(expires, str)

    def test_resend_letter(self):
        json_data = self.get_state()
        csrf_token = json_data['payload']['csrf_token']

        response = self.send_letter2(self.test_user_nin, csrf_token)
        self._check_success_response(response, type_='POST_LETTER_PROOFING_PROOFING_SUCCESS', msg=LetterMsg.letter_sent)

        csrf_token = response.json['payload']['csrf_token']
        response2 = self.send_letter2(self.test_user_nin, csrf_token)
        self._check_success_response(
            response2, type_='POST_LETTER_PROOFING_PROOFING_SUCCESS', msg=LetterMsg.already_sent
        )

        expires = response2.json['payload']['letter_expires']
        expires = datetime.utcfromtimestamp(int(expires))
        self.assertIsInstance(expires, datetime)
        expires = expires.strftime('%Y-%m-%d')
        self.assertIsInstance(expires, str)

    def test_send_letter_bad_csrf(self):
        response = self.send_letter2(self.test_user_nin, 'bad_csrf')
        self._check_error_response(response, type_='POST_LETTER_PROOFING_PROOFING_FAIL',
                                   error={'csrf_token': ['CSRF failed to validate']})

    def test_letter_sent_status(self):
        json_data = self.get_state()
        csrf_token = json_data['payload']['csrf_token']
        self.send_letter(self.test_user_nin, csrf_token)
        json_data = self.get_state()
        self.assertIn('letter_sent', json_data['payload'])
        expires = datetime.utcfromtimestamp(int(json_data['payload']['letter_expires']))
        self.assertIsInstance(expires, datetime)
        expires = expires.strftime('%Y-%m-%d')
        self.assertIsInstance(expires, str)

    def test_verify_letter_code(self):
        json_data = self.get_state()
        csrf_token = json_data['payload']['csrf_token']
        json_data = self.send_letter(self.test_user_nin, csrf_token)
        with self.app.test_request_context():
            with self.app.app_context():
                proofing_state = self.app.proofing_statedb.get_state_by_eppn(
                    self.test_user_eppn, raise_on_missing=False
                )
        csrf_token = json_data['payload']['csrf_token']
        response = self.verify_code2(proofing_state.nin.verification_code, csrf_token)
        # TODO: The payload incorrectly contains the NIN from before it was marked as verified.
        self._check_success_response(response, type_='POST_LETTER_PROOFING_VERIFY_CODE_SUCCESS',
                                     payload={'nins': [{'number': self.test_user_nin,
                                                        'primary': False,
                                                        'verified': False}],
                                              })

        user = self.app.private_userdb.get_user_by_eppn(self.test_user_eppn)
        self.assertEqual(user.nins.primary.number, self.test_user_nin)
        self.assertEqual(user.nins.primary.created_by, proofing_state.nin.created_by)
        self.assertEqual(user.nins.primary.verified_by, proofing_state.nin.created_by)
        self.assertEqual(user.nins.primary.is_verified, True)
        self.assertEqual(self.app.proofing_log.db_count(), 1)

    def test_verify_letter_code_bad_csrf(self):
        json_data = self.get_state()
        csrf_token = json_data['payload']['csrf_token']
        self.send_letter(self.test_user_nin, csrf_token)
        with self.app.test_request_context():
            with self.app.app_context():
                proofing_state = self.app.proofing_statedb.get_state_by_eppn(
                    self.test_user_eppn, raise_on_missing=False
                )
        response = self.verify_code2(proofing_state.nin.verification_code, 'bad_csrf')
        self._check_error_response(response, type_='POST_LETTER_PROOFING_VERIFY_CODE_FAIL',
                                   error={'csrf_token': ['CSRF failed to validate']})

    def test_verify_letter_code_fail(self):
        json_data = self.get_state()
        csrf_token = json_data['payload']['csrf_token']
        json_data = self.send_letter(self.test_user_nin, csrf_token)
        csrf_token = json_data['payload']['csrf_token']
        response = self.verify_code2('wrong code', csrf_token)
        self._check_error_response(response, type_='POST_LETTER_PROOFING_VERIFY_CODE_FAIL', msg=LetterMsg.wrong_code)

    def test_verify_letter_expired(self):
        json_data = self.get_state()
        csrf_token = json_data['payload']['csrf_token']
        json_data = self.send_letter(self.test_user_nin, csrf_token)
        with self.app.test_request_context():
            with self.app.app_context():
                proofing_state = self.app.proofing_statedb.get_state_by_eppn(
                    self.test_user_eppn, raise_on_missing=False
                )
                # move the proofing state back in time so that it is expired by now
                proofing_state.proofing_letter._data['sent_ts'] = None
                proofing_state.proofing_letter.sent_ts = datetime.fromisoformat('2020-01-01T01:02:03')
                self.app.proofing_statedb.save(proofing_state)
        csrf_token = json_data['payload']['csrf_token']
        response = self.verify_code2(proofing_state.nin.verification_code, csrf_token)
        self._check_error_response(
            response, type_='POST_LETTER_PROOFING_VERIFY_CODE_FAIL', msg=LetterMsg.letter_expired
        )

    def test_proofing_flow(self):
        json_data = self.get_state()
        csrf_token = json_data['payload']['csrf_token']
        self.send_letter(self.test_user_nin, csrf_token)
        self.get_state()
        json_data = self.get_state()
        csrf_token = json_data['payload']['csrf_token']
        with self.app.test_request_context():
            user = self.app.central_userdb.get_user_by_eppn(self.test_user_eppn, raise_on_missing=True)
            proofing_state = self.app.proofing_statedb.get_state_by_eppn(user.eppn, raise_on_missing=False)
        response = self.verify_code2(proofing_state.nin.verification_code, csrf_token)
        self._check_success_response(
            response, type_='POST_LETTER_PROOFING_VERIFY_CODE_SUCCESS', msg=LetterMsg.verify_success
        )

        user = self.app.private_userdb.get_user_by_eppn(self.test_user_eppn)
        self.assertEqual(user.nins.primary.number, self.test_user_nin)
        self.assertEqual(user.nins.primary.created_by, proofing_state.nin.created_by)
        self.assertEqual(user.nins.primary.verified_by, proofing_state.nin.created_by)
        self.assertEqual(user.nins.primary.is_verified, True)
        self.assertEqual(self.app.proofing_log.db_count(), 1)

    def test_proofing_flow_previously_added_nin(self):
        user = self.app.central_userdb.get_user_by_eppn(self.test_user_eppn)
        not_verified_nin = Nin.from_dict(
            dict(number=self.test_user_nin, created_by='test', verified=False, primary=False)
        )
        user.nins.add(not_verified_nin)
        self.app.central_userdb.save(user)

        json_data = self.get_state()
        csrf_token = json_data['payload']['csrf_token']
        self.send_letter(self.test_user_nin, csrf_token)
        self.get_state()
        json_data = self.get_state()
        csrf_token = json_data['payload']['csrf_token']
        with self.app.test_request_context():
            user = self.app.central_userdb.get_user_by_eppn(self.test_user_eppn, raise_on_missing=True)
            proofing_state = self.app.proofing_statedb.get_state_by_eppn(user.eppn, raise_on_missing=False)
        response = self.verify_code2(proofing_state.nin.verification_code, csrf_token)
        self._check_success_response(
            response, type_='POST_LETTER_PROOFING_VERIFY_CODE_SUCCESS', msg=LetterMsg.verify_success
        )

        user = self.app.private_userdb.get_user_by_eppn(self.test_user_eppn)
        self.assertEqual(user.nins.primary.number, self.test_user_nin)
        self.assertEqual(user.nins.primary.created_by, not_verified_nin.created_by)
        self.assertEqual(user.nins.primary.verified_by, proofing_state.nin.created_by)
        self.assertEqual(user.nins.primary.is_verified, True)
        self.assertEqual(self.app.proofing_log.db_count(), 1)

    def test_proofing_flow_previously_added_wrong_nin(self):
        json_data = self.get_state()
        csrf_token = json_data['payload']['csrf_token']
        # Send letter to correct nin
        self.send_letter(self.test_user_nin, csrf_token)

        # Remove correct unverified nin and add wrong nin
        user = self.app.central_userdb.get_user_by_eppn(self.test_user_eppn)
        user.nins.remove(self.test_user_nin)
        not_verified_nin = Nin.from_dict(
            dict(number=self.test_user_wrong_nin, created_by='test', verified=False, primary=False)
        )
        user.nins.add(not_verified_nin)
        self.app.central_userdb.save(user)

        # Time passes, user gets code in the mail. Enters code.
        json_data = self.get_state()
        csrf_token = json_data['payload']['csrf_token']
        with self.app.test_request_context():
            user = self.app.central_userdb.get_user_by_eppn(self.test_user_eppn, raise_on_missing=True)
            proofing_state = self.app.proofing_statedb.get_state_by_eppn(user.eppn, raise_on_missing=False)
        response = self.verify_code2(proofing_state.nin.verification_code, csrf_token)
        self._check_success_response(
            response, type_='POST_LETTER_PROOFING_VERIFY_CODE_SUCCESS', msg=LetterMsg.verify_success
        )

        # Now check that the (now verified) NIN on the user is back to the one used to request the letter
        user = self.app.private_userdb.get_user_by_eppn(self.test_user_eppn)
        self.assertEqual(user.nins.primary.number, self.test_user_nin)
        self.assertEqual(user.nins.primary.created_by, proofing_state.nin.created_by)
        self.assertEqual(user.nins.primary.verified_by, proofing_state.nin.created_by)
        self.assertEqual(user.nins.primary.is_verified, True)
        self.assertEqual(self.app.proofing_log.db_count(), 1)

    def test_expire_proofing_state(self):
        json_data = self.get_state()
        csrf_token = json_data['payload']['csrf_token']
        self.send_letter(self.test_user_nin, csrf_token)
        json_data = self.get_state()
        self.assertIn('letter_sent', json_data['payload'])
        self.app.config.letter_wait_time_hours = -24
        json_data = self.get_state()
        self.assertTrue(json_data['payload']['letter_expired'])
        self.assertIn('letter_sent', json_data['payload'])
        self.assertIsNotNone(json_data['payload']['letter_sent'])

    @patch('eduid_common.api.msg.MsgRelay.get_postal_address')
    def test_unmarshal_error(self, mock_get_postal_address):
        mock_get_postal_address.return_value = self.mock_address

        json_data = self.get_state()
        csrf_token = json_data['payload']['csrf_token']
        response = self.send_letter2('not a nin', csrf_token)

        self._check_error_response(response, type_='POST_LETTER_PROOFING_PROOFING_FAIL',
                                   error={'nin': ['nin needs to be formatted as 18|19|20yymmddxxxx']})

    @patch('eduid_common.api.am.AmRelay.request_user_sync')
    @patch('eduid_common.api.msg.MsgRelay.get_postal_address')
    def test_locked_identity_no_locked_identity(self, mock_get_postal_address, mock_request_user_sync):
        mock_get_postal_address.return_value = self.mock_address
        mock_request_user_sync.side_effect = self.request_user_sync
        user = self.app.central_userdb.get_user_by_eppn(self.test_user_eppn)
        self.assertEqual(user.locked_identity.count, 0)

        # User with no locked_identity
        with self.session_cookie(self.browser, self.test_user_eppn):
            json_data = self.get_state()
            csrf_token = json_data['payload']['csrf_token']
            response = self.send_letter2(self.test_user_nin, csrf_token)
        self._check_success_response(response, type_='POST_LETTER_PROOFING_PROOFING_SUCCESS',
                                   msg=LetterMsg.letter_sent)

    @patch('eduid_common.api.am.AmRelay.request_user_sync')
    @patch('eduid_common.api.msg.MsgRelay.get_postal_address')
    def test_locked_identity_correct_nin(self, mock_get_postal_address, mock_request_user_sync):
        mock_get_postal_address.return_value = self.mock_address
        mock_request_user_sync.side_effect = self.request_user_sync
        user = self.app.central_userdb.get_user_by_eppn(self.test_user_eppn)

        # User with locked_identity and correct nin
        user.locked_identity.add(
            LockedIdentityNin.from_dict(dict(number=self.test_user_nin, created_by='test', created_ts=True))
        )
        self.app.central_userdb.save(user, check_sync=False)
        with self.session_cookie(self.browser, self.test_user_eppn):
            json_data = self.get_state()
            csrf_token = json_data['payload']['csrf_token']
            response = self.send_letter2(self.test_user_nin, csrf_token)
        self._check_success_response(response, type_='POST_LETTER_PROOFING_PROOFING_SUCCESS',
                                   msg=LetterMsg.letter_sent)

    @patch('eduid_common.api.am.AmRelay.request_user_sync')
    @patch('eduid_common.api.msg.MsgRelay.get_postal_address')
    def test_locked_identity_incorrect_nin(self, mock_get_postal_address, mock_request_user_sync):
        mock_get_postal_address.return_value = self.mock_address
        mock_request_user_sync.side_effect = self.request_user_sync
        user = self.app.central_userdb.get_user_by_eppn(self.test_user_eppn)

        user.locked_identity.add(
            LockedIdentityNin.from_dict(dict(number=self.test_user_nin, created_by='test', created_ts=True))
        )
        self.app.central_userdb.save(user, check_sync=False)

        # User with locked_identity and incorrect nin
        with self.session_cookie(self.browser, self.test_user_eppn):
            json_data = self.get_state()
            csrf_token = json_data['payload']['csrf_token']
            response = self.send_letter2('200102031234', csrf_token)
        self._check_error_response(response, type_='POST_LETTER_PROOFING_PROOFING_FAIL',
                                   payload={'message': 'Another nin is already registered for this user'
                                                       })

    def test_get_code_backdoor(self):
        self.app.config.magic_cookie = 'magic-cookie'
        self.app.config.magic_cookie_name = 'magic'
        self.app.config.environment = 'dev'

        response = self.get_code_backdoor()
        state = self.app.proofing_statedb.get_state_by_eppn(self.test_user_eppn)

        self.assertEqual(response.data.decode('ascii'), state.nin.verification_code)

    def test_get_code_no_backdoor_in_pro(self):
        self.app.config.magic_cookie = 'magic-cookie'
        self.app.config.magic_cookie_name = 'magic'
        self.app.config.environment = 'pro'

        response = self.get_code_backdoor()

        self.assertEqual(response.status_code, 400)

    def test_get_code_no_backdoor_without_cookie(self):
        self.app.config.magic_cookie = 'magic-cookie'
        self.app.config.magic_cookie_name = 'magic'
        self.app.config.environment = 'dev'

        response = self.get_code_backdoor(add_cookie=False)

        self.assertEqual(response.status_code, 400)

    def test_get_code_no_backdoor_misconfigured1(self):
        self.app.config.magic_cookie = 'magic-cookie'
        self.app.config.magic_cookie_name = ''
        self.app.config.environment = 'dev'

        response = self.get_code_backdoor()

        self.assertEqual(response.status_code, 400)

    def test_get_code_no_backdoor_misconfigured2(self):
        self.app.config.magic_cookie = ''
        self.app.config.magic_cookie_name = 'magic'
        self.app.config.environment = 'dev'

        response = self.get_code_backdoor()

        self.assertEqual(response.status_code, 400)

    def test_get_code_no_backdoor_wrong_value(self):
        self.app.config.magic_cookie = 'magic-cookie'
        self.app.config.magic_cookie_name = 'magic'
        self.app.config.environment = 'dev'

        response = self.get_code_backdoor(cookie_value='wrong-cookie')

        self.assertEqual(response.status_code, 400)
