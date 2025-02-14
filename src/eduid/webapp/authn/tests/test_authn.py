#
# Copyright (c) 2016 NORDUnet A/S
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

import base64
import json
import logging
import os
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Tuple
from urllib.parse import quote_plus

from flask import Blueprint
from saml2.s_utils import deflate_and_base64_encode
from werkzeug.exceptions import NotFound
from werkzeug.http import dump_cookie

from eduid.common.config.parsers import load_config
from eduid.common.misc.timeutil import utc_now
from eduid.common.utils import urlappend
from eduid.webapp.authn.app import AuthnApp, authn_init_app
from eduid.webapp.authn.settings.common import AuthnConfig
from eduid.webapp.common.api.testing import EduidAPITestCase
from eduid.webapp.common.authn.acs_enums import AuthnAcsAction
from eduid.webapp.common.authn.cache import OutstandingQueriesCache
from eduid.webapp.common.authn.eduid_saml2 import get_authn_request
from eduid.webapp.common.authn.middleware import AuthnBaseApp
from eduid.webapp.common.authn.tests.responses import auth_response, logout_request, logout_response
from eduid.webapp.common.authn.utils import get_location, no_authn_views
from eduid.webapp.common.session import EduidSession, session
from eduid.webapp.common.session.namespaces import AuthnRequestRef

logger = logging.getLogger(__name__)

HERE = os.path.abspath(os.path.dirname(__file__))


@dataclass
class AcsResult:
    session: EduidSession
    authn_ref: AuthnRequestRef


class AuthnAPITestBase(EduidAPITestCase):
    """Test cases for the real eduid-authn app"""

    app: AuthnApp

    def update_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Called from the parent class, so that we can update the configuration
        according to the needs of this test case.
        """
        saml_config = os.path.join(HERE, "saml2_settings.py")
        config.update(
            {
                "safe_relay_domain": "test.localhost",
                "saml2_login_redirect_url": "/",
                "saml2_logout_redirect_url": "/logged-out",
                "saml2_settings_module": saml_config,
                "saml2_strip_saml_user_suffix": "@test.eduid.se",
                "signup_authn_failure_redirect_url": "http://test.localhost/failure",
                "signup_authn_success_redirect_url": "http://test.localhost/success",
            }
        )
        return config

    def load_app(self, test_config: Mapping[str, Any]) -> AuthnApp:
        """
        Called from the parent class, so we can provide the appropriate flask
        app for this test case.
        """
        return authn_init_app(test_config=test_config)

    def add_outstanding_query(self, came_from: str) -> str:
        """
        Add a SAML2 authentication query to the queries cache.
        To be used before accessing the assertion consumer service.

        :param came_from: url to redirect back the client
                          after finishing with the authn service.

        :return: the session token corresponding to the query
        """
        with self.app.test_request_context("/login"):
            self.app.dispatch_request()
            oq_cache = OutstandingQueriesCache(session.authn.sp.pysaml2_dicts)
            cookie_val = session.meta.cookie_val
            oq_cache.set(cookie_val, came_from)
            session.persist()  # Explicit session.persist is needed when working within a test_request_context
            return cookie_val

    def login(self, eppn: str, came_from: str) -> str:
        """
        Add a SAML2 authentication query to the queries cache,
        build a cookie with a session id corresponding to the added query,
        build a SAML2 authn response for the added query,
        and send both to the assertion consumer service,
        so that the user is logged in (the session corresponding to the cookie
        has her eppn).
        This method returns the cookie that has to be sent with any
        subsequent request that needs to be authenticated.

        :param eppn: the eppn of the user to be logged in
        :param came_from: url to redirect back the client
                          after finishing with the authn service.

        :return: the cookie corresponding to the authn session
        """
        res = self.acs("/login", eppn=eppn, next_url=came_from)
        cookie = res.session.meta.cookie_val
        logger.debug(f"Test logged in, got cookie {cookie}")
        return self.dump_session_cookie(cookie)

    def authn(self, url: str, force_authn: bool = False, next_url: str = "/", expect_url_allowed: bool = True) -> None:
        """
        Common code for the tests that need to send an authentication request.
        This checks that the client is redirected to the idp.

        :param url: the url of the desired authentication mode.
        :param force_authn: whether to force re-authentication for an already
                            authenticated client
        :param next_url: Next url
        """
        with self.session_cookie_anon(self.browser) as browser:
            _url = f"{url}?next={quote_plus(next_url)}"
            logger.debug(f"Test fetching {_url}")
            resp = browser.get(_url)
            logger.debug(f"Test fetched {_url}, response {resp}")
            assert resp.status_code == 302

            with browser.session_transaction() as sess:
                request_id, authn_ref = self._get_request_id_from_session(sess)
                logger.debug(f"Test ACS got SAML request id {request_id} from session {sess}")

                # save the authn_data for further checking below
                authn = sess.authn.sp.authns[authn_ref]

                # Create another mock authn request, presumably only to get the IdP URL below
                authn_req = get_location(
                    get_authn_request(
                        saml2_config=self.app.saml2_config,
                        session=sess,
                        relay_state="",
                        authn_id=AuthnRequestRef(str(uuid.uuid4())),
                        selected_idp=None,
                        force_authn=force_authn,
                    )
                )

        idp_url = authn_req.split("?")[0]
        assert resp.status_code == 302
        assert resp.location.startswith(idp_url)
        logger.debug(f"Test got the expected redirect to the IdP {idp_url}")
        if expect_url_allowed:
            assert authn.redirect_url == next_url
        else:
            # When the next_url isn't accepted as safe to use, a redirect to '/' is done instead
            assert authn.redirect_url == "/"

    def _get_request_id_from_session(self, session: EduidSession) -> Tuple[str, AuthnRequestRef]:
        """extract the (probable) SAML request ID from the session"""
        oq_cache = OutstandingQueriesCache(session.authn.sp.pysaml2_dicts)
        ids = oq_cache.outstanding_queries().keys()
        if len(ids) != 1:
            raise RuntimeError("More or less than one authn request in the session")
        saml_req_id = list(ids)[0]
        req_ref = AuthnRequestRef(oq_cache.outstanding_queries()[saml_req_id])
        return saml_req_id, req_ref

    def acs(self, url: str, eppn: str, next_url: str = "/camefrom/", expect_url_allowed: bool = True) -> AcsResult:
        """
        common code for the tests that need to access the assertion consumer service
        and then check the side effects of this access.

        :param url: the url of the desired authentication mode.
        :param eppn: the eppn of the user to access the service
        :param next_url: Relay state
        :param expect_url_allowed: True if the next_url is expected to be accepted
        """
        with self.session_cookie_anon(self.browser) as browser:
            _url = f"{url}?next={quote_plus(next_url)}"
            logger.debug(f"Test fetching {_url}")
            resp = browser.get(_url)
            logger.debug(f"Test fetched {_url}, response {resp}")
            assert resp.status_code == 302

            with browser.session_transaction() as sess:
                request_id, authn_ref = self._get_request_id_from_session(sess)
                logger.debug(f"Test ACS got SAML request id {request_id} from session {sess}")

            authr = auth_response(request_id, eppn).encode("utf-8")
            data = {
                "csrf": sess.get_csrf_token(),
                "SAMLResponse": base64.b64encode(authr),
            }

            resp = browser.post("/saml2-acs", data=data)

            assert resp.status_code == 302
            if expect_url_allowed:
                assert resp.location == urlappend("http://test.localhost", next_url)
            else:
                # When the next_url isn't accepted as safe to use, a redirect to '/' is done instead
                assert resp.location == "http://test.localhost/"
            with browser.session_transaction() as sess:
                return AcsResult(session=sess, authn_ref=authn_ref)

    def dump_session_cookie(self, session_id: str) -> str:
        """
        Get a cookie corresponding to an authenticated session.

        :param session_id: the token for the session

        :return: the cookie
        """
        return dump_cookie(
            self.app.conf.flask.session_cookie_name,
            session_id,
            max_age=float(self.app.conf.flask.permanent_session_lifetime),
            path=self.app.conf.flask.session_cookie_path,
            domain=self.app.conf.flask.session_cookie_domain,
        )


class AuthnAPITestCase(AuthnAPITestBase):
    """
    Tests to check the different modes of authentication.
    """

    app: AuthnApp

    def setUp(self):
        super().setUp(users=["hubba-bubba", "hubba-fooo"])

    def test_login_authn(self):
        self.authn("/login")

    def test_login_authn_good_relay_state(self):
        self.authn("/login", next_url="http://test.localhost/profile/")

    def test_login_authn_bad_relay_state(self):
        self.authn("/login", next_url="http://bad.localhost/evil/", expect_url_allowed=False)

    def test_chpass_authn(self):
        self.authn("/chpass", force_authn=True)

    def test_terminate_authn(self):
        self.authn("/terminate", force_authn=True)

    def test_login_assertion_consumer_service(self):
        eppn = "hubba-bubba"

        res = self.acs("/login", eppn)
        assert res.session.common.eppn == "hubba-bubba"

    def test_login_assertion_consumer_service_good_relay_state(self):
        eppn = "hubba-bubba"

        res = self.acs("/login", eppn, next_url="/profile/")
        assert res.session.common.eppn == "hubba-bubba"

    def test_login_assertion_consumer_service_bad_relay_state(self):
        eppn = "hubba-bubba"

        self.acs("/login", eppn, next_url="http://bad.localhost/evil/", expect_url_allowed=False)

    def test_chpass_assertion_consumer_service(self):
        res = self.acs("/chpass", self.test_user.eppn)
        assert "reauthn-for-chpass" not in res.session  # this was the old method
        assert res.session.common.eppn == self.test_user.eppn
        assert res.session.common.is_logged_in is True
        authn = res.session.authn.sp.authns[res.authn_ref]
        assert authn.post_authn_action == AuthnAcsAction.change_password
        assert authn.authn_instant is not None
        age = utc_now() - authn.authn_instant
        assert 10 < age.total_seconds() < 15

    def test_terminate_assertion_consumer_service(self):
        res = self.acs("/terminate", self.test_user.eppn)
        assert res.session.common.eppn == self.test_user.eppn
        assert res.session.common.is_logged_in == True
        authn = res.session.authn.sp.authns[res.authn_ref]
        assert authn.post_authn_action == AuthnAcsAction.terminate_account
        assert authn.authn_instant is not None
        age = utc_now() - authn.authn_instant
        assert 10 < age.total_seconds() < 15

    def _signup_authn_user(self, eppn):
        timestamp = utc_now()

        with self.app.test_client() as c:
            with self.app.test_request_context("/signup-authn"):
                c.set_cookie(
                    "test.localhost", key=self.app.conf.flask.session_cookie_name, value=session.meta.cookie_val[16:]
                )
                session.common.eppn = eppn
                session.signup.ts = timestamp

                return self.app.dispatch_request()

    def test_signup_authn_new_user(self):
        eppn = "hubba-fooo"
        resp = self._signup_authn_user(eppn)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.location.startswith(self.app.conf.signup_authn_success_redirect_url))

    def test_signup_authn_old_user(self):
        """A user that has verified their account should not try to use token login"""
        eppn = "hubba-bubba"
        resp = self._signup_authn_user(eppn)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.location.startswith(self.app.conf.signup_authn_failure_redirect_url))


class AuthnTestApp(AuthnBaseApp):
    def __init__(self, config: AuthnConfig, **kwargs):
        super().__init__(config, **kwargs)
        self.conf = config


class UnAuthnAPITestCase(EduidAPITestCase):
    """Tests for a fictitious app based on AuthnBaseApp"""

    app: AuthnTestApp

    def update_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Called from the parent class, so that we can update the configuration
        according to the needs of this test case.
        """
        saml_config = os.path.join(HERE, "saml2_settings.py")
        config.update(
            {
                "saml2_login_redirect_url": "/",
                "saml2_logout_redirect_url": "/",
                "saml2_settings_module": saml_config,
                "saml2_strip_saml_user_suffix": "@test.eduid.se",
                "token_service_url": "http://login",
            }
        )
        return config

    def load_app(self, test_config: Mapping[str, Any]) -> AuthnTestApp:
        """
        Called from the parent class, so we can provide the appropriate flask
        app for this test case.
        """
        config = load_config(typ=AuthnConfig, app_name="testing", ns="webapp", test_config=test_config)
        return AuthnTestApp(config)

    def test_no_cookie(self):
        with self.app.test_client() as c:
            resp = c.get("/")
            self.assertEqual(resp.status_code, 302)
            self.assertTrue(resp.location.startswith(self.app.conf.token_service_url))

    def test_cookie(self):
        sessid = "fb1f42420b0109020203325d750185673df252de388932a3957f522a6c43a" "a47"
        self.redis_instance.conn.set(sessid, json.dumps({"v1": {"id": "0"}}))

        with self.session_cookie(self.browser, self.test_user.eppn) as c:
            self.assertRaises(NotFound, c.get, "/")


class NoAuthnAPITestCase(EduidAPITestCase):
    """Tests for a fictitious app based on AuthnBaseApp"""

    app: AuthnTestApp

    def setUp(self):
        super(NoAuthnAPITestCase, self).setUp()
        test_views = Blueprint("testing", __name__)

        @test_views.route("/test")
        def test():
            return "OK"

        @test_views.route("/test2")
        def test2():
            return "OK"

        @test_views.route("/test3")
        def test3():
            return "OK"

        self.app.register_blueprint(test_views)

    def update_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Called from the parent class, so that we can update the configuration
        according to the needs of this test case.
        """
        saml_config = os.path.join(HERE, "saml2_settings.py")
        config.update(
            {
                "no_authn_urls": ["^/test$"],
                "saml2_login_redirect_url": "/",
                "saml2_logout_redirect_url": "/",
                "saml2_settings_module": saml_config,
                "saml2_strip_saml_user_suffix": "@test.eduid.se",
                "token_service_url": "http://login",
            }
        )
        return config

    def load_app(self, test_config: Mapping[str, Any]) -> AuthnTestApp:
        """
        Called from the parent class, so we can provide the appropriate flask
        app for this test case.
        """
        config = load_config(typ=AuthnConfig, app_name="testing", ns="webapp", test_config=test_config)
        return AuthnTestApp(config)

    def test_no_authn(self):
        with self.app.test_client() as c:
            resp = c.get("/test")
            self.assertEqual(resp.status_code, 200)

    def test_authn(self):
        with self.app.test_client() as c:
            resp = c.get("/test2")
            self.assertEqual(resp.status_code, 302)
            self.assertTrue(resp.location.startswith(self.app.conf.token_service_url))

    def test_no_authn_util(self):
        no_authn_urls_before = [path for path in self.app.conf.no_authn_urls]
        no_authn_path = "/test3"
        no_authn_views(self.app.conf, [no_authn_path])
        self.assertEqual(no_authn_urls_before + ["^{!s}$".format(no_authn_path)], self.app.conf.no_authn_urls)

        with self.app.test_client() as c:
            resp = c.get("/test3")
            self.assertEqual(resp.status_code, 200)


class LogoutRequestTests(AuthnAPITestBase):
    def test_metadataview(self):
        with self.app.test_client() as c:
            response = c.get("/saml2-metadata")
            self.assertEqual(response.status, "200 OK")

    def test_logout_nologgedin(self):
        eppn = "hubba-bubba"
        with self.app.test_request_context("/logout", method="GET"):
            # eppn is set in the IdP
            session.common.eppn = eppn
            response = self.app.dispatch_request()
            self.assertEqual(response.status, "302 FOUND")
            self.assertIn(self.app.conf.saml2_logout_redirect_url, response.headers["Location"])

    def test_logout_loggedin(self):
        cookie = self.login(eppn=self.test_user.eppn, came_from="/afterlogin/")

        with self.app.test_request_context("/logout", method="GET", headers={"Cookie": cookie}):
            response = self.app.dispatch_request()
            logger.debug(f"Test called /logout, response {response}")
            self.assertEqual(response.status, "302 FOUND")
            self.assertIn(
                "https://idp.example.com/simplesaml/saml2/idp/SingleLogoutService.php", response.headers["location"]
            )

    def test_logout_service_startingSP(self):

        came_from = "/afterlogin/"
        session_id = self.add_outstanding_query(came_from)
        cookie = self.dump_session_cookie(session_id)

        with self.app.test_request_context(
            "/saml2-ls",
            method="POST",
            headers={"Cookie": cookie},
            data={
                "SAMLResponse": deflate_and_base64_encode(logout_response(session_id)),
                "RelayState": "/testing-relay-state",
            },
        ):
            response = self.app.dispatch_request()

            self.assertEqual(response.status, "302 FOUND")
            self.assertIn("testing-relay-state", response.location)

    def test_logout_service_startingSP_already_logout(self):

        came_from = "/afterlogin/"
        session_id = self.add_outstanding_query(came_from)

        with self.app.test_request_context(
            "/saml2-ls",
            method="POST",
            data={
                "SAMLResponse": deflate_and_base64_encode(logout_response(session_id)),
                "RelayState": "/testing-relay-state",
            },
        ):
            response = self.app.dispatch_request()

            self.assertEqual(response.status, "302 FOUND")
            self.assertIn("testing-relay-state", response.location)

    def test_logout_service_startingIDP(self):

        res = self.acs("/login", eppn=self.test_user.eppn, next_url="/afterlogin/")
        cookie = self.dump_session_cookie(res.session.meta.cookie_val)

        with self.app.test_request_context(
            "/saml2-ls",
            method="POST",
            headers={"Cookie": cookie},
            data={
                "SAMLRequest": deflate_and_base64_encode(logout_request("SESSION_ID")),
                "RelayState": "/testing-relay-state",
            },
        ):
            response = self.app.dispatch_request()

            self.assertEqual(response.status, "302 FOUND")
            assert (
                "https://idp.example.com/simplesaml/saml2/idp/SingleLogoutService.php?SAMLResponse="
                in response.location
            )

    def test_logout_service_startingIDP_no_subject_id(self):

        eppn = "hubba-bubba"
        came_from = "/afterlogin/"
        session_id = self.add_outstanding_query(came_from)
        cookie = self.dump_session_cookie(session_id)

        saml_response = auth_response(session_id, eppn).encode("utf-8")

        # Log in through IDP SAMLResponse
        with self.app.test_request_context(
            "/saml2-acs",
            method="POST",
            headers={"Cookie": cookie},
            data={
                "SAMLResponse": base64.b64encode(saml_response),
                "RelayState": "/testing-relay-state",
            },
        ):
            self.app.dispatch_request()
            session.persist()  # Explicit session.persist is needed when working within a test_request_context

        with self.app.test_request_context(
            "/saml2-ls",
            method="POST",
            headers={"Cookie": cookie},
            data={
                "SAMLRequest": deflate_and_base64_encode(logout_request(session_id)),
                "RelayState": "/testing-relay-state",
            },
        ):
            session.authn.name_id = None
            session.persist()  # Explicit session.persist is needed when working within a test_request_context
            response = self.app.dispatch_request()

            self.assertEqual(response.status, "302 FOUND")
            self.assertIn("testing-relay-state", response.location)
