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
"""
Configuration (file) handling for the eduID reset_password app.
"""
from datetime import timedelta

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


class ResetPasswordConfig(
    EduIDBaseAppConfig,
    WebauthnConfigMixin2,
    MagicCookieMixin,
    AmConfigMixin,
    MsgConfigMixin,
    MailConfigMixin,
    PasswordConfigMixin,
):
    """
    Configuration for the reset_password app
    """

    app_name: str = "reset_password"

    # VCCS URL
    vccs_url: str
    dashboard_url: str

    email_code_timeout: timedelta = Field(default=timedelta(hours=2))
    phone_code_timeout: timedelta = Field(default=timedelta(minutes=10))
    # Number of bytes of salt to generate (recommended min 16).
    password_salt_length: int = 32
    # Length of H1 hash to produce (recommended min 32).
    password_hash_length: int = 32
    # bcrypt pbkdf number of rounds.
    # For number of rounds, it is recommended that a measurement is made to achieve
    # a cost of at least 100 ms on current hardware.
    password_generation_rounds: int = 2**5
    # throttle resend of mail and sms
    throttle_resend: timedelta = Field(default=timedelta(minutes=5))
    # URL to get the js app that can drive the process to reset the password
    password_reset_link: str = "https://www.eduid.se/reset-password/email-code"
    password_service_url: str = "/services/reset-password/"
    # Throttle sending SMSs for extra security resetting passwords
    throttle_sms: timedelta = Field(default=timedelta(minutes=5))
    eduid_site_url: str = "https://www.eduid.se"
    eduid_site_name: str = "eduID"
