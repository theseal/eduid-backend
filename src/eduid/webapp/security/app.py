# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 NORDUnet A/S
# Copyright (c) 2020 SUNET
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

from typing import Any, Mapping, Optional, cast

from fido_mds import FidoMetadataStore
from flask import current_app

from eduid.common.config.parsers import load_config
from eduid.common.rpc.am_relay import AmRelay
from eduid.common.rpc.mail_relay import MailRelay
from eduid.common.rpc.msg_relay import MsgRelay
from eduid.userdb.authninfo import AuthnInfoDB
from eduid.userdb.logs import ProofingLog
from eduid.userdb.logs.db import FidoMetadataLog
from eduid.userdb.security import PasswordResetStateDB, SecurityUserDB
from eduid.webapp.common.api import translation
from eduid.webapp.common.authn.middleware import AuthnBaseApp
from eduid.webapp.security.settings.common import SecurityConfig


class SecurityApp(AuthnBaseApp):
    def __init__(self, config: SecurityConfig, **kwargs):
        super().__init__(config, **kwargs)

        self.conf = config

        self.am_relay = AmRelay(config)
        self.msg_relay = MsgRelay(config)
        self.mail_relay = MailRelay(config)

        self.fido_mds = FidoMetadataStore()

        self.private_userdb = SecurityUserDB(config.mongo_uri)
        self.authninfo_db = AuthnInfoDB(config.mongo_uri)
        self.password_reset_state_db = PasswordResetStateDB(config.mongo_uri)
        self.proofing_log = ProofingLog(config.mongo_uri)
        self.fido_metadata_log = FidoMetadataLog(config.mongo_uri)

        self.babel = translation.init_babel(self)


current_security_app: SecurityApp = cast(SecurityApp, current_app)


def security_init_app(name: str = "security", test_config: Optional[Mapping[str, Any]] = None) -> SecurityApp:
    """
    Create an instance of an eduid security (passwords) app.

    :param name: The name of the instance, it will affect the configuration loaded.
    :param test_config: Override config. Used in test cases.
    """
    config = load_config(typ=SecurityConfig, app_name=name, ns="webapp", test_config=test_config)

    app = SecurityApp(config)

    app.logger.info(f"Init {app}...")

    from eduid.webapp.security.views.change_password import change_password_views
    from eduid.webapp.security.views.security import security_views
    from eduid.webapp.security.views.webauthn import webauthn_views

    app.register_blueprint(security_views)
    app.register_blueprint(webauthn_views)
    app.register_blueprint(change_password_views)

    return app
