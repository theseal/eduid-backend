# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 SUNET
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
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import PurePath
from typing import Any, Dict, List, Mapping, Optional

from bson import ObjectId
from flask import Response as FlaskResponse
from saml2 import BINDING_HTTP_POST, BINDING_HTTP_REDIRECT
from saml2.client import Saml2Client
from saml2.response import AuthnResponse

from eduid.common.misc.timeutil import utc_now
from eduid.userdb import ToUEvent
from eduid.webapp.common.api.testing import EduidAPITestCase
from eduid.webapp.common.authn.cache import IdentityCache, OutstandingQueriesCache, StateCache
from eduid.webapp.common.authn.utils import get_saml2_config
from eduid.webapp.idp.app import IdPApp, init_idp_app
from eduid.webapp.idp.helpers import IdPAction
from eduid.webapp.idp.sso_session import SSOSession

__author__ = "ft"


logger = logging.getLogger(__name__)


@dataclass
class GenericResult:
    payload: Dict[str, Any]


@dataclass
class NextResult(GenericResult):
    pass


@dataclass
class PwAuthResult(GenericResult):
    sso_cookie_val: Optional[str] = None
    cookies: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TouResult(GenericResult):
    pass


@dataclass
class FinishedResultAPI(GenericResult):
    pass


@dataclass
class LoginResultAPI:
    response: FlaskResponse
    ref: Optional[str] = None
    sso_cookie_val: Optional[str] = None
    visit_count: Dict[str, int] = field(default_factory=dict)
    visit_order: List[IdPAction] = field(default_factory=list)
    pwauth_result: Optional[PwAuthResult] = None
    tou_result: Optional[TouResult] = None
    finished_result: Optional[FinishedResultAPI] = None


class IdPAPITests(EduidAPITestCase):
    """Base TestCase for those tests that need a full environment setup"""

    def setUp(
        self,
        *args,
        **kwargs,
    ):
        super().setUp(*args, **kwargs)
        self.idp_entity_id = "https://unittest-idp.example.edu/idp.xml"
        self.relay_state = "test-fest"
        self.sp_config = get_saml2_config(self.app.conf.pysaml2_config, name="SP_CONFIG")
        # pysaml2 likes to keep state about ongoing logins, data from login to when you logout etc.
        self._pysaml2_caches: Dict[str, Any] = dict()
        self.pysaml2_state = StateCache(self._pysaml2_caches)  # _saml2_state in _pysaml2_caches
        self.pysaml2_identity = IdentityCache(self._pysaml2_caches)  # _saml2_identities in _pysaml2_caches
        self.pysaml2_oq = OutstandingQueriesCache(self._pysaml2_caches)  # _saml2_outstanding_queries in _pysaml2_caches
        self.saml2_client = Saml2Client(config=self.sp_config, identity_cache=self.pysaml2_identity)

    def load_app(self, config: Optional[Mapping[str, Any]]) -> IdPApp:
        """
        Called from the parent class, so we can provide the appropriate flask
        app for this test case.
        """
        return init_idp_app(test_config=config)

    def update_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        config = super().update_config(config)
        fn = PurePath(__file__).with_name("data") / "test_SSO_conf.py"
        config.update(
            {
                "pysaml2_config": str(fn),
                "fticks_secret_key": "test test",
                "eduperson_targeted_id_secret_key": "eptid_secret",
                "sso_cookie": {"key": "test_sso_cookie"},
                "eduid_site_url": "https://eduid.docker_dev",
                "u2f_app_id": "https://example.com",
                "u2f_valid_facets": ["https://dashboard.dev.eduid.se", "https://idp.dev.eduid.se"],
                "fido2_rp_id": "idp.example.com",
                "login_bundle_url": "https://idp.eduid.docker/test-bundle",
                "tou_version": "2016-v1",
                "other_device_secret_key": "lx0sg0g21QUkiu9JAPfhx4hJ5prJtbk1PPE-OBvpiAk=",
                "known_devices_secret_key": "WwemHQgPm1hpx41NYaVBQpRV7BAq0OMtfF3k4H72J7c=",
                "geo_statistics_secret_key": "gk5cBWIZ6k-mNHWnA33ZpsgXfgH50Wi_s3mUNI9GF0o=",
            }
        )
        return config

    def _try_login(
        self,
        saml2_client: Optional[Saml2Client] = None,
        authn_context=None,
        force_authn: bool = False,
        assertion_consumer_service_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> LoginResultAPI:
        """
        Try logging in to the IdP.

        :return: Information about how far we got (reached LoginState) and the last response instance.
        """
        _saml2_client = saml2_client if saml2_client is not None else self.saml2_client

        (session_id, info) = _saml2_client.prepare_for_authenticate(
            entityid=self.idp_entity_id,
            relay_state=self.relay_state,
            binding=BINDING_HTTP_REDIRECT,
            requested_authn_context=authn_context,
            force_authn=force_authn,
            assertion_consumer_service_url=assertion_consumer_service_url,
        )
        self.pysaml2_oq.set(session_id, self.relay_state)

        path = self._extract_path_from_info(info)
        with self.session_cookie_anon(self.browser) as browser:
            # Send SAML request to SAML endpoint, expect a redirect to the login bundle back
            resp = browser.get(path)
            if resp.status_code != 302:
                return LoginResultAPI(response=resp)

            redirect_loc = self._extract_path_from_response(resp)
            ref = redirect_loc.split("/")[-1]

            result = LoginResultAPI(ref=ref, response=resp)

            cookie_jar = {}

            while True:
                logger.info(f"Main API test loop, current state: {result}")

                # Call the 'next' endpoint
                _next = self._call_next(ref)

                _action = IdPAction(_next.payload["action"])
                if _action not in result.visit_count:
                    result.visit_count[_action] = 0
                result.visit_count[_action] += 1
                result.visit_order += [_action]

                if result.visit_count[_action] > 1:
                    # break on re-visiting a previous state
                    logger.error(f"Next state {_action} already visited, aborting with result {result}")
                    return result

                if _action == IdPAction.PWAUTH:
                    if not username or not password:
                        logger.error(f"Can't login without username and password, aborting with result {result}")
                        return result

                    result.pwauth_result = self._call_pwauth(_next.payload["target"], ref, username, password)
                    result.sso_cookie_val = result.pwauth_result.sso_cookie_val
                    cookie_jar.update(result.pwauth_result.cookies)

                if _action == IdPAction.MFA:
                    # Not implemented yet
                    return result

                if _action == IdPAction.TOU:
                    result.tou_result = self._call_tou(
                        _next.payload["target"], ref, user_accepts=self.app.conf.tou_version
                    )

                if _action == IdPAction.FINISHED:
                    result.finished_result = FinishedResultAPI(payload=_next.payload)
                    return result

    def _call_next(self, ref: str) -> NextResult:
        with self.session_cookie_anon(self.browser) as client:
            with self.app.test_request_context():
                with client.session_transaction() as sess:
                    data = {"ref": ref, "csrf_token": sess.get_csrf_token()}
                response = client.post("/next", data=json.dumps(data), content_type=self.content_type_json)
        logger.debug(f"Next endpoint returned:\n{json.dumps(response.json, indent=4)}")
        return NextResult(payload=response.json["payload"])

    def _call_pwauth(self, target: str, ref: str, username: str, password: str) -> PwAuthResult:
        with self.session_cookie_anon(self.browser) as client:
            with self.app.test_request_context():
                with client.session_transaction() as sess:
                    data = {"ref": ref, "username": username, "password": password, "csrf_token": sess.get_csrf_token()}
                response = client.post(target, data=json.dumps(data), content_type=self.content_type_json)
        logger.debug(f"PwAuth endpoint returned:\n{json.dumps(response.json, indent=4)}")

        result = PwAuthResult(payload=response.json["payload"])
        cookies = response.headers.get("Set-Cookie")
        if not cookies:
            return result

        # Save the SSO cookie value
        _re = f".*{self.app.conf.sso_cookie.key}=(.+?);.*"
        _sso_cookie_re = re.match(_re, cookies)
        if _sso_cookie_re:
            result.sso_cookie_val = _sso_cookie_re.groups()[0]

        if result.sso_cookie_val:
            result.cookies = {self.app.conf.sso_cookie.key: result.sso_cookie_val}

        return result

    def _call_tou(self, target: str, ref: str, user_accepts=Optional[str]) -> TouResult:
        with self.session_cookie_anon(self.browser) as client:
            with self.app.test_request_context():
                with client.session_transaction() as sess:
                    data = {"ref": ref, "csrf_token": sess.get_csrf_token()}
                    if user_accepts:
                        data["user_accepts"] = user_accepts
                response = client.post(target, data=json.dumps(data), content_type=self.content_type_json)
        logger.debug(f"ToU endpoint returned:\n{json.dumps(response.json, indent=4)}")
        result = TouResult(payload=response.json["payload"])
        return result

    @staticmethod
    def _extract_form_inputs(res: str) -> Dict[str, Any]:
        inputs = {}
        for line in res.split("\n"):
            if "input" in line:
                # YOLO
                m = re.match(".*<input .* name=['\"](.+?)['\"].*value=['\"](.+?)['\"]", line)
                if m:
                    name, value = m.groups()
                    inputs[name] = value.strip("'\"")
        return inputs

    def _extract_path_from_response(self, response: FlaskResponse) -> str:
        return self._extract_path_from_info({"headers": response.headers})

    def _extract_path_from_info(self, info: Mapping[str, Any]) -> str:
        _location_headers = [_hdr for _hdr in info["headers"] if _hdr[0] == "Location"]
        # get first Location URL
        loc = _location_headers[0][1]
        return self._extract_path_from_url(loc)

    def _extract_path_from_url(self, url):
        # It is a complete URL, extract the path from it (8 is to skip over slashes in https://)
        _idx = url[8:].index("/")
        path = url[8 + _idx :]
        return path

    def parse_saml_authn_response(
        self, response: FlaskResponse, saml2_client: Optional[Saml2Client] = None
    ) -> AuthnResponse:
        _saml2_client = saml2_client if saml2_client is not None else self.saml2_client

        form = self._extract_form_inputs(response.data.decode("utf-8"))
        xmlstr = bytes(form["SAMLResponse"], "ascii")
        outstanding_queries = self.pysaml2_oq.outstanding_queries()
        return _saml2_client.parse_authn_request_response(xmlstr, BINDING_HTTP_POST, outstanding_queries)

    def get_sso_session(self, sso_cookie_val: str) -> Optional[SSOSession]:
        if sso_cookie_val is None:
            return None
        return self.app.sso_sessions.get_session(sso_cookie_val)

    def add_test_user_tou(self, version: Optional[str] = None) -> ToUEvent:
        """Utility function to add a valid ToU to the default test user"""
        if version is None:
            version = self.app.conf.tou_version
        tou = ToUEvent(
            version=version,
            created_by="idp_tests",
            created_ts=utc_now(),
            modified_ts=utc_now(),
            event_id=str(ObjectId()),
        )
        self.test_user.tou.add(tou)
        self.amdb.save(self.test_user, check_sync=False)
        return tou
