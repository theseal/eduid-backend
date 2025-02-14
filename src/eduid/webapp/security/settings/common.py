# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 NORDUnet A/S
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
from datetime import timedelta
from typing import List, Optional

from fido2.webauthn import AttestationConveyancePreference
from fido_mds.models.fido_mds import AuthenticatorStatus
from pydantic import Field

from eduid.common.config.base import (
    AmConfigMixin,
    EduIDBaseAppConfig,
    MagicCookieMixin,
    MailConfigMixin,
    MsgConfigMixin,
    PasswordConfigMixin,
    WebauthnConfigMixin2,
)


class SecurityConfig(
    EduIDBaseAppConfig,
    WebauthnConfigMixin2,
    MagicCookieMixin,
    AmConfigMixin,
    MsgConfigMixin,
    MailConfigMixin,
    PasswordConfigMixin,
):
    """
    Configuration for the security app
    """

    app_name: str = "security"

    vccs_url: str
    dashboard_url: str
    token_service_url: str
    throttle_update_user_period: timedelta = Field(default=timedelta(seconds=600))

    # change password
    chpass_reauthn_timeout: timedelta = Field(default=timedelta(seconds=120))
    chpass_old_password_needed: bool = True

    # webauthn
    webauthn_proofing_method = Field(default="webauthn metadata")
    webauthn_proofing_version = Field(default="2022v1")
    webauthn_max_allowed_tokens: int = 10
    webauthn_attestation: Optional[AttestationConveyancePreference] = None
    webauthn_allowed_user_verification_methods: List[str] = Field(
        default=[
            "faceprint_internal",
            "passcode_external",
            "passcode_internal",
            "handprint_internal",
            "pattern_internal",
            "voiceprint_internal",
            "fingerprint_internal",
            "eyeprint_internal",
            "apple",
        ]
    )
    webauthn_allowed_key_protection: List[str] = Field(
        default=["remote_handle", "hardware", "secure_element", "tee", "apple"]
    )
    webauthn_allowed_status: List[AuthenticatorStatus] = Field(
        default=[
            AuthenticatorStatus.FIDO_CERTIFIED,
            AuthenticatorStatus.FIDO_CERTIFIED_L1,
            AuthenticatorStatus.FIDO_CERTIFIED_L2,
            AuthenticatorStatus.FIDO_CERTIFIED_L3,
            AuthenticatorStatus.FIDO_CERTIFIED_L1plus,
            AuthenticatorStatus.FIDO_CERTIFIED_L2plus,
            AuthenticatorStatus.FIDO_CERTIFIED_L3plus,
        ]
    )

    # for logging out when terminating an account
    logout_endpoint: str = "/services/authn/logout"
    # URL to send the user to after terminating the account
    termination_redirect_url: str = "https://eduid.se"
    eduid_site_url: str = "https://www.eduid.se"
    eduid_site_name: str = "eduID"
