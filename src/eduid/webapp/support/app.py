# -*- coding: utf-8 -*-
#
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
#     3. Neither the name of the SUNET nor the names of its
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
import operator
from typing import Any, Mapping, Optional, cast

from flask import current_app
from jinja2.exceptions import UndefinedError

from eduid.common.config.parsers import load_config
from eduid.common.utils import urlappend
from eduid.userdb.support import db
from eduid.webapp.common.authn.middleware import AuthnBaseApp
from eduid.webapp.support.settings.common import SupportConfig


class SupportApp(AuthnBaseApp):
    def __init__(self, config: SupportConfig, **kwargs):
        super().__init__(config, **kwargs)

        self.conf = config

        self.support_user_db = db.SupportUserDB(config.mongo_uri)
        self.support_authn_db = db.SupportAuthnInfoDB(config.mongo_uri)
        self.support_proofing_log_db = db.SupportProofingLogDB(config.mongo_uri)
        self.support_signup_db = db.SupportSignupUserDB(config.mongo_uri)
        self.support_letter_proofing_db = db.SupportLetterProofingDB(config.mongo_uri)
        self.support_oidc_proofing_db = db.SupportOidcProofingDB(config.mongo_uri)
        self.support_email_proofing_db = db.SupportEmailProofingDB(config.mongo_uri)
        self.support_phone_proofing_db = db.SupportPhoneProofingDB(config.mongo_uri)


current_support_app: SupportApp = cast(SupportApp, current_app)


def register_template_funcs(app: SupportApp) -> None:
    @app.template_filter("datetimeformat")
    def datetimeformat(value, format="%Y-%m-%d %H:%M %Z"):
        if not value:
            return ""
        return value.strftime(format)

    @app.template_filter("dateformat")
    def dateformat(value, format="%Y-%m-%d"):
        if not value:
            return ""
        return value.strftime(format)

    @app.template_filter("multisort")
    def sort_multi(l, *operators, **kwargs):
        # Don't try to sort on missing keys
        keys = list(operators)  # operators is immutable
        for key in operators:
            for item in l:
                if key not in item:
                    app.logger.debug("Removed key {} before sorting.".format(key))
                    keys.remove(key)
                    break
        reverse = kwargs.pop("reverse", False)
        try:
            l.sort(key=operator.itemgetter(*keys), reverse=reverse)
        except UndefinedError:  # attribute did not exist
            l = list()
        return l

    @app.template_global()
    def static_url_for(f: str, version: Optional[str] = None) -> str:
        """
        Get the static url for a file and optionally have a version argument appended for cache busting.
        """
        static_url = current_support_app.conf.eduid_static_url
        if version is not None:
            static_url = urlappend(static_url, version)
        return urlappend(static_url, f)

    return None


def support_init_app(name: str = "support", test_config: Optional[Mapping[str, Any]] = None) -> SupportApp:
    """
    Create an instance of an eduid support app.

    :param name: The name of the instance, it will affect the configuration loaded.
    :param test_config: Override config, used in test cases.
    """
    config = load_config(typ=SupportConfig, app_name=name, ns="webapp", test_config=test_config)

    app = SupportApp(config)

    app.logger.info(f"Init {app}...")

    from eduid.webapp.support.views import support_views

    app.register_blueprint(support_views)

    register_template_funcs(app)

    return app
