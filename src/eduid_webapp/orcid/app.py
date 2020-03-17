# -*- coding: utf-8 -*-
#
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
from typing import cast

from flask import current_app

from eduid_userdb.proofing import OrcidProofingStateDB, OrcidProofingUserDB
from eduid_userdb.logs import ProofingLog
from eduid_common.api import am, oidc
from eduid_common.authn.middleware import AuthnBaseApp
from eduid_webapp.orcid.settings.common import OrcidConfig

__author__ = 'lundberg'


class OrcidApp(AuthnBaseApp):

    def __init__(self, name: str, config: dict, **kwargs):

        super(OrcidApp, self).__init__(name, OrcidConfig, config, **kwargs)

        # Register views
        from eduid_webapp.orcid.views import orcid_views
        self.register_blueprint(orcid_views)

        # Init dbs
        self.private_userdb = OrcidProofingUserDB(self.config.mongo_uri)
        self.proofing_statedb = OrcidProofingStateDB(self.config.mongo_uri)
        self.proofing_log = ProofingLog(self.config.mongo_uri)

        # Init celery
        am.init_relay(self, 'eduid_orcid')

        # Initialize the oidc_client
        oidc.init_client(self)


current_orcid_app: OrcidApp = cast(OrcidApp, current_app)


def init_orcid_app(name: str, config: dict) -> OrcidApp:
    """
    :param name: The name of the instance, it will affect the configuration loaded.
    :param config: any additional configuration settings. Specially useful
                   in test cases
    """

    app = OrcidApp(name, config)

    app.logger.info(f'Init {name} app...')

    return app
