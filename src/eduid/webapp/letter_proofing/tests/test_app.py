# -*- coding: utf-8 -*-


import json
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any, Optional

from flask import Response
from mock import Mock, patch

from eduid.userdb import NinIdentity
from eduid.userdb.identity import IdentityType
from eduid.webapp.common.api.testing import EduidAPITestCase
from eduid.webapp.letter_proofing.app import init_letter_proofing_app
from eduid.webapp.letter_proofing.helpers import LetterMsg

__author__ = "lundberg"


class LetterProofingTests(EduidAPITestCase):
    """Base TestCase for those tests that need a full environment setup"""

    def setUp(self):
        self.test_user_eppn = "hubba-baar"
        self.test_user_nin = "200001023456"
        self.test_user_wrong_nin = "190001021234"
        self.mock_address = OrderedDict(
            [
                (
                    "Name",
                    OrderedDict([("GivenNameMarking", "20"), ("GivenName", "Testaren Test"), ("Surname", "Testsson")]),
                ),
                (
                    "OfficialAddress",
                    OrderedDict([("Address2", "\xd6RGATAN 79 LGH 10"), ("PostalCode", "12345"), ("City", "LANDET")]),
                ),
            ]
        )
        super(LetterProofingTests, self).setUp(users=["hubba-baar"])

    @staticmethod
    def mock_response(status_code=200, content=None, json_data=None, headers=None, raise_for_status=None):
        """
        since we typically test a bunch of different
        requests calls for a service, we are going to do
        a lot of mock responses, so its usually a good idea
        to have a helper function that builds these things
        """
        if headers is None:
            headers = {}
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
        return init_letter_proofing_app("testing", config)

    def update_config(self, app_config):
        app_config.update(
            {
                # 'ekopost_debug_pdf': devnull,
                "ekopost_api_uri": "http://localhost",
                "ekopost_api_user": "ekopost_user",
                "ekopost_api_pw": "secret",
                "letter_wait_time_hours": 336,
            }
        )
        return app_config

    # Helper methods
    def get_state(self):
        with self.session_cookie(self.browser, self.test_user_eppn) as client:
            response = client.get("/proofing")
        self.assertEqual(response.status_code, 200)
        return json.loads(response.data)

    def send_letter(self, nin: str, csrf_token: Optional[str] = None, validate_response=True) -> Response:
        """
        Invoke the POST /proofing endpoint, check that the HTTP response code is 200 and return the response.

        To be used with the data validation functions _check_success_response and _check_error_response.
        """
        response = self._send_letter2(nin, csrf_token)
        if validate_response:
            self._check_success_response(
                response, type_="POST_LETTER_PROOFING_PROOFING_SUCCESS", msg=LetterMsg.letter_sent
            )
        return response

    @patch("hammock.Hammock._request")
    @patch("eduid.common.rpc.am_relay.AmRelay.request_user_sync")
    @patch("eduid.common.rpc.msg_relay.MsgRelay.get_postal_address")
    def _send_letter2(
        self, nin: str, csrf_token: Optional[str], mock_get_postal_address, mock_request_user_sync, mock_hammock
    ):
        if csrf_token is None:
            _state = self.get_state()
            csrf_token = _state["payload"]["csrf_token"]

        ekopost_response = self.mock_response(json_data={"id": "test"})
        mock_hammock.return_value = ekopost_response
        mock_request_user_sync.side_effect = self.request_user_sync
        mock_get_postal_address.return_value = self.mock_address
        data = {"nin": nin, "csrf_token": csrf_token}
        with self.session_cookie(self.browser, self.test_user_eppn) as client:
            response = client.post("/proofing", data=json.dumps(data), content_type=self.content_type_json)
        return response

    def verify_code(self, code: str, csrf_token: Optional[str] = None, validate_response=True) -> Response:
        """
        Invoke the POST /verify-code endpoint, check that the HTTP response code is 200 and return the response.

        To be used with the data validation functions _check_success_response and _check_error_response.
        """
        response = self._verify_code2(code, csrf_token)
        if validate_response:
            self._check_success_response(
                response, type_="POST_LETTER_PROOFING_VERIFY_CODE_SUCCESS", msg=LetterMsg.verify_success
            )
        return response

    @patch("eduid.common.rpc.am_relay.AmRelay.request_user_sync")
    @patch("eduid.common.rpc.msg_relay.MsgRelay.get_postal_address")
    def _verify_code2(self, code: str, csrf_token: Optional[str], mock_get_postal_address, mock_request_user_sync):
        if csrf_token is None:
            _state = self.get_state()
            csrf_token = _state["payload"]["csrf_token"]

        mock_request_user_sync.side_effect = self.request_user_sync
        mock_get_postal_address.return_value = self.mock_address
        data = {"code": code, "csrf_token": csrf_token}
        with self.session_cookie(self.browser, self.test_user_eppn) as client:
            response = client.post("/verify-code", data=json.dumps(data), content_type=self.content_type_json)
        return response

    @patch("hammock.Hammock._request")
    @patch("eduid.common.rpc.am_relay.AmRelay.request_user_sync")
    @patch("eduid.common.rpc.msg_relay.MsgRelay.get_postal_address")
    def get_code_backdoor(
        self,
        mock_get_postal_address: Any,
        mock_request_user_sync: Any,
        mock_hammock: Any,
        cookie_value: Optional[str] = None,
        add_cookie: bool = True,
    ):
        ekopost_response = self.mock_response(json_data={"id": "test"})
        mock_hammock.return_value = ekopost_response
        mock_request_user_sync.side_effect = self.request_user_sync
        mock_get_postal_address.return_value = self.mock_address

        nin = self.test_user_nin
        json_data = self.get_state()
        csrf_token = json_data["payload"]["csrf_token"]
        data = {"nin": nin, "csrf_token": csrf_token}

        with self.session_cookie(self.browser, self.test_user_eppn) as client:
            response = client.post("/proofing", data=json.dumps(data), content_type=self.content_type_json)
            self.assertEqual(response.status_code, 200)

            if cookie_value is None:
                cookie_value = self.app.conf.magic_cookie

            if add_cookie:
                client.set_cookie("localhost", key=self.app.conf.magic_cookie_name, value=cookie_value)

            return client.get("/get-code")

    # End helper methods

    def test_authenticate(self):
        response = self.browser.get("/proofing")
        self.assertEqual(response.status_code, 302)  # Redirect to token service
        with self.session_cookie(self.browser, self.test_user_eppn) as client:
            response = client.get("/proofing")
        self.assertEqual(response.status_code, 200)  # Authenticated request

    def test_letter_not_sent_status(self):
        json_data = self.get_state()
        assert json_data["payload"]["message"] == LetterMsg.no_state.value

    def test_send_letter(self):
        response = self.send_letter(self.test_user_nin)
        expires = response.json["payload"]["letter_expires"]
        expires = datetime.fromisoformat(expires)
        self.assertIsInstance(expires, datetime)
        # Check that the user was given until midnight the day the code expires
        assert expires.hour == 23
        assert expires.minute == 59
        assert expires.second == 59

    def test_resend_letter(self):
        response = self.send_letter(self.test_user_nin)

        # Deliberately test the CSRF token from the send_letter response,
        # instead of always using get_state() to get a token.
        csrf_token = response.json["payload"]["csrf_token"]
        response2 = self.send_letter(self.test_user_nin, csrf_token, validate_response=False)
        self._check_success_response(
            response2, type_="POST_LETTER_PROOFING_PROOFING_SUCCESS", msg=LetterMsg.already_sent
        )

        expires = response2.json["payload"]["letter_expires"]
        expires = datetime.fromisoformat(expires)
        self.assertIsInstance(expires, datetime)
        expires = expires.strftime("%Y-%m-%d")
        self.assertIsInstance(expires, str)

    def test_send_letter_bad_csrf(self):
        response = self.send_letter(self.test_user_nin, "bad_csrf", validate_response=False)
        self._check_error_response(
            response, type_="POST_LETTER_PROOFING_PROOFING_FAIL", error={"csrf_token": ["CSRF failed to validate"]}
        )

    def test_letter_sent_status(self):
        self.send_letter(self.test_user_nin)
        json_data = self.get_state()
        self.assertIn("letter_sent", json_data["payload"])
        expires = datetime.fromisoformat(json_data["payload"]["letter_expires"])
        self.assertIsInstance(expires, datetime)
        expires = expires.strftime("%Y-%m-%d")
        self.assertIsInstance(expires, str)

    def test_verify_letter_code(self):
        response1 = self.send_letter(self.test_user_nin)
        proofing_state = self.app.proofing_statedb.get_state_by_eppn(self.test_user_eppn)
        # Deliberately test the CSRF token from the send_letter response,
        # instead of always using get_state() to get a token.
        csrf_token = response1.json["payload"]["csrf_token"]
        response2 = self.verify_code(proofing_state.nin.verification_code, csrf_token)
        self._check_success_response(
            response2,
            type_="POST_LETTER_PROOFING_VERIFY_CODE_SUCCESS",
            payload={
                "nins": [{"number": self.test_user_nin, "primary": True, "verified": True}],
                "identities": {
                    "is_verified": True,
                    "nin": {
                        "number": self.test_user_nin,
                        "verified": True,
                    },
                },
            },
        )

        # TODO: When LogElements have working from_dict/to_dict, implement a proofing_log.get_proofings_by_eppn()
        #       and work on the returned LetterProofing instance instead of with a mongo document
        log_docs = self.app.proofing_log._get_documents_by_attr("eduPersonPrincipalName", self.test_user_eppn)
        assert 1 == len(log_docs)

        user = self.app.private_userdb.get_user_by_eppn(self.test_user_eppn)
        self._check_nin_verified_ok(user=user, proofing_state=proofing_state, number=self.test_user_nin)

    def test_verify_letter_code_bad_csrf(self):
        self.send_letter(self.test_user_nin)
        proofing_state = self.app.proofing_statedb.get_state_by_eppn(self.test_user_eppn)
        response = self.verify_code(proofing_state.nin.verification_code, "bad_csrf", validate_response=False)
        self._check_error_response(
            response, type_="POST_LETTER_PROOFING_VERIFY_CODE_FAIL", error={"csrf_token": ["CSRF failed to validate"]}
        )

    def test_verify_letter_code_fail(self):
        self.send_letter(self.test_user_nin)
        response = self.verify_code("wrong code", validate_response=False)
        self._check_error_response(response, type_="POST_LETTER_PROOFING_VERIFY_CODE_FAIL", msg=LetterMsg.wrong_code)

    def test_verify_letter_expired(self):
        response = self.send_letter(self.test_user_nin)
        # move the proofing state back in time so that it is expired by now
        proofing_state = self.app.proofing_statedb.get_state_by_eppn(self.test_user_eppn)
        proofing_state.proofing_letter.sent_ts = datetime.fromisoformat("2020-01-01T01:02:03")
        self.app.proofing_statedb.save(proofing_state)

        csrf_token = response.json["payload"]["csrf_token"]
        response = self.verify_code(proofing_state.nin.verification_code, csrf_token, validate_response=False)
        self._check_error_response(
            response, type_="POST_LETTER_PROOFING_VERIFY_CODE_FAIL", msg=LetterMsg.letter_expired
        )

    def test_proofing_flow(self):
        self.send_letter(self.test_user_nin)
        self.get_state()
        proofing_state = self.app.proofing_statedb.get_state_by_eppn(self.test_user_eppn)
        self.verify_code(proofing_state.nin.verification_code, None)

        user = self.app.private_userdb.get_user_by_eppn(self.test_user_eppn)
        self._check_nin_verified_ok(user=user, proofing_state=proofing_state, number=self.test_user_nin)

    def test_proofing_flow_previously_added_nin(self):
        user = self.app.central_userdb.get_user_by_eppn(self.test_user_eppn)
        not_verified_nin = NinIdentity(number=self.test_user_nin, created_by="test", is_verified=False)
        user.identities.add(not_verified_nin)
        self.app.central_userdb.save(user)

        self.send_letter(self.test_user_nin)
        proofing_state = self.app.proofing_statedb.get_state_by_eppn(user.eppn)
        self.verify_code(proofing_state.nin.verification_code, None)

        user = self.app.private_userdb.get_user_by_eppn(self.test_user_eppn)
        self._check_nin_verified_ok(
            user=user, proofing_state=proofing_state, number=self.test_user_nin, created_by=not_verified_nin.created_by
        )

    def test_proofing_flow_previously_added_wrong_nin(self):
        # Send letter to correct nin
        self.send_letter(self.test_user_nin)

        # Remove correct unverified nin and add wrong nin
        user = self.app.central_userdb.get_user_by_eppn(self.test_user_eppn)
        user.identities.remove(IdentityType.NIN)
        not_verified_nin = NinIdentity(number=self.test_user_wrong_nin, created_by="test", is_verified=False)
        user.identities.add(not_verified_nin)
        self.app.central_userdb.save(user)

        # Time passes, user gets code in the mail. Enters code.
        proofing_state = self.app.proofing_statedb.get_state_by_eppn(user.eppn)
        self.verify_code(proofing_state.nin.verification_code, None)

        # Now check that the (now verified) NIN on the user is back to the one used to request the letter
        user = self.app.central_userdb.get_user_by_eppn(self.test_user_eppn)
        self._check_nin_verified_ok(user=user, proofing_state=proofing_state, number=self.test_user_nin)

    def test_expire_proofing_state(self):
        self.send_letter(self.test_user_nin)
        json_data = self.get_state()
        self.assertIn("letter_sent", json_data["payload"])
        self.app.conf.letter_wait_time_hours = -24
        json_data = self.get_state()
        self.assertTrue(json_data["payload"]["letter_expired"])
        self.assertIn("letter_sent", json_data["payload"])
        self.assertIsNotNone(json_data["payload"]["letter_sent"])

    def test_send_new_letter_with_expired_proofing_state(self):
        self.send_letter(self.test_user_nin)
        json_data = self.get_state()
        self.assertIn("letter_sent", json_data["payload"])
        self.app.conf.letter_wait_time_hours = -24
        self.send_letter(self.test_user_nin)
        self.assertFalse(json_data["payload"]["letter_expired"])
        self.assertIn("letter_sent", json_data["payload"])
        self.assertIsNotNone(json_data["payload"]["letter_sent"])

    @patch("eduid.common.rpc.msg_relay.MsgRelay.get_postal_address")
    def test_unmarshal_error(self, mock_get_postal_address):
        mock_get_postal_address.return_value = self.mock_address

        response = self.send_letter("not a nin", validate_response=False)

        self._check_error_response(
            response,
            type_="POST_LETTER_PROOFING_PROOFING_FAIL",
            error={"nin": ["nin needs to be formatted as 18|19|20yymmddxxxx"]},
        )

    @patch("eduid.common.rpc.am_relay.AmRelay.request_user_sync")
    @patch("eduid.common.rpc.msg_relay.MsgRelay.get_postal_address")
    def test_locked_identity_no_locked_identity(self, mock_get_postal_address, mock_request_user_sync):
        mock_get_postal_address.return_value = self.mock_address
        mock_request_user_sync.side_effect = self.request_user_sync
        user = self.app.central_userdb.get_user_by_eppn(self.test_user_eppn)
        self.assertEqual(user.locked_identity.count, 0)

        # User with no locked_identity
        with self.session_cookie(self.browser, self.test_user_eppn):
            self.send_letter(self.test_user_nin)

    @patch("eduid.common.rpc.am_relay.AmRelay.request_user_sync")
    @patch("eduid.common.rpc.msg_relay.MsgRelay.get_postal_address")
    def test_locked_identity_correct_nin(self, mock_get_postal_address, mock_request_user_sync):
        mock_get_postal_address.return_value = self.mock_address
        mock_request_user_sync.side_effect = self.request_user_sync
        user = self.app.central_userdb.get_user_by_eppn(self.test_user_eppn)

        # User with locked_identity and correct nin
        user.locked_identity.add(NinIdentity(number=self.test_user_nin, created_by="test", is_verified=True))
        self.app.central_userdb.save(user, check_sync=False)
        with self.session_cookie(self.browser, self.test_user_eppn):
            response = self.send_letter(self.test_user_nin)

    @patch("eduid.common.rpc.am_relay.AmRelay.request_user_sync")
    @patch("eduid.common.rpc.msg_relay.MsgRelay.get_postal_address")
    def test_locked_identity_incorrect_nin(self, mock_get_postal_address, mock_request_user_sync):
        mock_get_postal_address.return_value = self.mock_address
        mock_request_user_sync.side_effect = self.request_user_sync
        user = self.app.central_userdb.get_user_by_eppn(self.test_user_eppn)

        user.locked_identity.add(NinIdentity(number=self.test_user_nin, created_by="test", is_verified=True))
        self.app.central_userdb.save(user, check_sync=False)

        # User with locked_identity and incorrect nin
        with self.session_cookie(self.browser, self.test_user_eppn):
            response = self.send_letter("200102031234", validate_response=False)
        self._check_error_response(
            response,
            type_="POST_LETTER_PROOFING_PROOFING_FAIL",
            payload={"message": "Another nin is already registered for this user"},
        )

    @patch("hammock.Hammock._request")
    @patch("eduid.common.rpc.am_relay.AmRelay.request_user_sync")
    def test_send_letter_backdoor(self, mock_request_user_sync, mock_hammock):
        self.app.conf.magic_cookie = "magic-cookie"
        self.app.conf.magic_cookie_name = "magic"
        self.app.conf.environment = "dev"

        ekopost_response = self.mock_response(json_data={"id": "test"})
        mock_hammock.return_value = ekopost_response
        mock_request_user_sync.side_effect = self.request_user_sync

        _state = self.get_state()
        csrf_token = _state["payload"]["csrf_token"]
        data = {"nin": self.test_user_nin, "csrf_token": csrf_token}
        with self.session_cookie(self.browser, self.test_user_eppn) as client:
            client.set_cookie("localhost", key=self.app.conf.magic_cookie_name, value=self.app.conf.magic_cookie)
            response = client.post("/proofing", data=json.dumps(data), content_type=self.content_type_json)
        self._check_success_response(response, type_="POST_LETTER_PROOFING_PROOFING_SUCCESS", msg=LetterMsg.letter_sent)

    def test_get_code_backdoor(self):
        self.app.conf.magic_cookie = "magic-cookie"
        self.app.conf.magic_cookie_name = "magic"
        self.app.conf.environment = "dev"

        response = self.get_code_backdoor()
        state = self.app.proofing_statedb.get_state_by_eppn(self.test_user_eppn)

        self.assertEqual(response.data.decode("ascii"), state.nin.verification_code)

    def test_get_code_no_backdoor_in_pro(self):
        self.app.conf.magic_cookie = "magic-cookie"
        self.app.conf.magic_cookie_name = "magic"
        self.app.conf.environment = "production"

        response = self.get_code_backdoor()

        self.assertEqual(response.status_code, 400)

    def test_get_code_no_backdoor_without_cookie(self):
        self.app.conf.magic_cookie = "magic-cookie"
        self.app.conf.magic_cookie_name = "magic"
        self.app.conf.environment = "dev"

        response = self.get_code_backdoor(add_cookie=False)

        self.assertEqual(response.status_code, 400)

    def test_get_code_no_backdoor_misconfigured1(self):
        self.app.conf.magic_cookie = "magic-cookie"
        self.app.conf.magic_cookie_name = ""
        self.app.conf.environment = "dev"

        response = self.get_code_backdoor()

        self.assertEqual(response.status_code, 400)

    def test_get_code_no_backdoor_misconfigured2(self):
        self.app.conf.magic_cookie = ""
        self.app.conf.magic_cookie_name = "magic"
        self.app.conf.environment = "dev"

        response = self.get_code_backdoor()

        self.assertEqual(response.status_code, 400)

    def test_get_code_no_backdoor_wrong_value(self):
        self.app.conf.magic_cookie = "magic-cookie"
        self.app.conf.magic_cookie_name = "magic"
        self.app.conf.environment = "dev"

        response = self.get_code_backdoor(cookie_value="wrong-cookie")

        self.assertEqual(response.status_code, 400)

    def test_state_days_info(self):
        """Validate calculation of days information in state retrieval"""
        self.send_letter(self.test_user_nin)
        json_data = self.get_state()

        assert json_data["payload"]["letter_sent_days_ago"] == 0
        assert json_data["payload"]["letter_expires_in_days"] == 14
        assert json_data["payload"]["letter_expired"] is False
        assert json_data["payload"]["message"] == LetterMsg.already_sent.value

        proofing_state = self.app.proofing_statedb.get_state_by_eppn(self.test_user_eppn)

        # move back the 'letter sent' value to the last second of yesterday
        new_ts = proofing_state.proofing_letter.sent_ts - timedelta(days=1)
        new_ts = new_ts.replace(hour=23, minute=59, second=59)
        proofing_state.proofing_letter.sent_ts = new_ts
        self.app.proofing_statedb.save(proofing_state)

        json_data = self.get_state()

        assert json_data["payload"]["letter_sent_days_ago"] == 1
        assert json_data["payload"]["letter_expires_in_days"] == 13
        assert json_data["payload"]["letter_expired"] is False
        assert json_data["payload"]["message"] == LetterMsg.already_sent.value

        # move back the 'letter sent' value to the last day of validity
        new_ts = proofing_state.proofing_letter.sent_ts - timedelta(days=13)
        new_ts = new_ts.replace(hour=23, minute=59, second=59)
        proofing_state.proofing_letter.sent_ts = new_ts
        self.app.proofing_statedb.save(proofing_state)

        json_data = self.get_state()

        assert json_data["payload"]["letter_sent_days_ago"] == 14
        assert json_data["payload"]["letter_expires_in_days"] == 0
        assert json_data["payload"]["letter_expired"] is False
        assert json_data["payload"]["message"] == LetterMsg.already_sent.value

        # make the state expired
        new_ts = proofing_state.proofing_letter.sent_ts - timedelta(days=1)
        new_ts = new_ts.replace(hour=23, minute=59, second=59)
        proofing_state.proofing_letter.sent_ts = new_ts
        self.app.proofing_statedb.save(proofing_state)

        json_data = self.get_state()

        assert json_data["payload"]["letter_sent_days_ago"] == 15
        assert "letter_expires_in_days" not in json_data["payload"]
        assert json_data["payload"]["letter_expired"] is True
        assert json_data["payload"]["message"] == LetterMsg.letter_expired.value

    def test_proofing_with_a_verified_nin(self):
        """Test that no letter is sent when the user already has a verified NIN"""
        user = self.app.central_userdb.get_user_by_eppn(self.test_user_eppn)
        verified_nin = NinIdentity(number=self.test_user_nin, created_by="test", is_verified=True, verified_by="test")
        user.identities.add(verified_nin)
        self.app.central_userdb.save(user)

        response = self.send_letter(self.test_user_nin, validate_response=False)
        self._check_error_response(
            response,
            type_="POST_LETTER_PROOFING_PROOFING_FAIL",
            payload={"message": "User is already verified"},
        )

        proofing_state = self.app.proofing_statedb.get_state_by_eppn(user.eppn)
        assert proofing_state is None
