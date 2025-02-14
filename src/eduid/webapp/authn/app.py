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
from typing import Any, Mapping, Optional

from flask import current_app

from eduid.common.config.parsers import load_config
from eduid.webapp.authn.settings.common import AuthnConfig
from eduid.webapp.common.api.app import EduIDBaseApp
from eduid.webapp.common.authn.utils import get_saml2_config


class AuthnApp(EduIDBaseApp):
    def __init__(self, config: AuthnConfig, **kwargs):
        super().__init__(config, **kwargs)

        self.conf = config

        self.saml2_config = get_saml2_config(config.saml2_settings_module)


def get_current_app() -> AuthnApp:
    """Teach pycharm about AuthnApp"""
    return current_app  # type: ignore


current_authn_app = get_current_app()


def authn_init_app(name: str = "authn", test_config: Optional[Mapping[str, Any]] = None) -> AuthnApp:
    """
    Create an instance of an authentication app.

    :param name: The name of the instance, it will affect the configuration file
                 loaded from the filesystem.
    :param test_config: any additional configuration settings. Specially useful
                   in test cases
    """
    config = load_config(typ=AuthnConfig, app_name=name, ns="webapp", test_config=test_config)

    app = AuthnApp(config)

    app.logger.info(f"Init {app}...")

    from eduid.webapp.authn.views import authn_views

    app.register_blueprint(authn_views)

    return app
