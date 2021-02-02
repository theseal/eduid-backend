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

from flask import current_app

from eduid_common.api import am, msg
from eduid_common.authn.middleware import AuthnBaseApp
from eduid_common.config.base import FlaskConfig
from eduid_common.config.parsers import load_config
from eduid_userdb.logs import ProofingLog
from eduid_userdb.proofing import PhoneProofingStateDB, PhoneProofingUserDB

from eduid_webapp.phone.settings.common import PhoneConfig


class PhoneApp(AuthnBaseApp):
    def __init__(self, name: str, test_config: Optional[Mapping[str, Any]], **kwargs):
        self.conf = load_config(typ=PhoneConfig, app_name=name, ns='webapp', test_config=test_config)
        # Initialise type of self.config before any parent class sets a precedent to mypy
        self.config = FlaskConfig.init_config(ns='webapp', app_name=name, test_config=test_config)
        super().__init__(name, **kwargs)

        from eduid_webapp.phone.views import phone_views

        self.register_blueprint(phone_views)

        am.init_relay(self, 'eduid_phone')
        msg.init_relay(self)

        self.private_userdb = PhoneProofingUserDB(self.config.mongo_uri)
        self.proofing_statedb = PhoneProofingStateDB(self.config.mongo_uri)
        self.proofing_log = ProofingLog(self.config.mongo_uri)


current_phone_app: PhoneApp = cast(PhoneApp, current_app)


def phone_init_app(name: str, test_config: Optional[Mapping[str, Any]]) -> PhoneApp:
    """
    Create an instance of an eduid phone app.

    :param name: The name of the instance, it will affect the configuration loaded.
    :param config: any additional configuration settings. Specially useful
                   in test cases
    """

    app = PhoneApp(name, test_config)

    app.logger.info(f'Init {name} app...')

    return app
