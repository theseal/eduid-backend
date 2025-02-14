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
from typing import Any, Mapping, Optional, cast

from flask import current_app

from eduid.common.config.parsers import load_config
from eduid.common.rpc.am_relay import AmRelay
from eduid.common.rpc.msg_relay import MsgRelay
from eduid.userdb.logs import ProofingLog
from eduid.userdb.proofing import LetterProofingStateDB, LetterProofingUserDB
from eduid.webapp.common.api import translation
from eduid.webapp.common.authn.middleware import AuthnBaseApp
from eduid.webapp.letter_proofing.ekopost import Ekopost
from eduid.webapp.letter_proofing.settings.common import LetterProofingConfig

__author__ = "lundberg"


class LetterProofingApp(AuthnBaseApp):
    def __init__(self, config: LetterProofingConfig, **kwargs: Any):
        super().__init__(config, **kwargs)

        self.conf = config

        # Init dbs
        self.private_userdb = LetterProofingUserDB(config.mongo_uri)
        self.proofing_statedb = LetterProofingStateDB(config.mongo_uri)
        self.proofing_log = ProofingLog(config.mongo_uri)

        # Init celery
        self.msg_relay = MsgRelay(config)
        self.am_relay = AmRelay(config)

        # Init babel
        self.babel = translation.init_babel(self)

        # Initiate external modules
        self.ekopost = Ekopost(config)


current_letterp_app = cast(LetterProofingApp, current_app)


def init_letter_proofing_app(
    name: str = "letter_proofing", test_config: Optional[Mapping[str, Any]] = None
) -> LetterProofingApp:
    """
    :param name: The name of the instance, it will affect the configuration loaded.
    :param test_config: Override config, used in test cases.
    """
    config = load_config(typ=LetterProofingConfig, app_name=name, ns="webapp", test_config=test_config)

    app = LetterProofingApp(config)

    app.logger.info(f"Init {name} app...")

    # Register views
    from eduid.webapp.letter_proofing.views import letter_proofing_views

    app.register_blueprint(letter_proofing_views)

    return app
