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

from marshmallow import Schema, fields

from eduid.webapp.common.api.schemas.base import EduidSchema, FluxStandardAction
from eduid.webapp.common.api.schemas.csrf import CSRFRequestMixin, CSRFResponseMixin

__author__ = "ft"


class IdPRequest(EduidSchema, CSRFRequestMixin):
    ref = fields.Str(required=True)
    this_device = fields.Str(required=False)
    remember_me = fields.Bool(required=False)  # set to false when user requests we forget this_device


class NextRequestSchema(IdPRequest):
    pass


class NextResponseSchema(FluxStandardAction):
    class NextResponsePayload(EduidSchema, CSRFResponseMixin):
        class AuthnOptionsResponsePayload(EduidSchema):
            display_name = fields.Str(required=False)
            forced_username = fields.Str(required=False)
            freja_eidplus = fields.Bool(required=True)
            has_session = fields.Bool(required=True)
            is_reauthn = fields.Bool(required=True)
            other_device = fields.Bool(required=True)
            password = fields.Bool(required=True)
            username = fields.Bool(required=False)
            usernamepassword = fields.Bool(required=False)
            webauthn = fields.Bool(required=True)

        class ServiceInfoResponsePayload(EduidSchema):
            display_name = fields.Dict(keys=fields.Str(), values=fields.Str(), required=False)

        action = fields.Str(required=True)
        target = fields.Str(required=True)
        parameters = fields.Dict(keys=fields.Str(), required=False)
        authn_options = fields.Nested(AuthnOptionsResponsePayload, required=False)
        service_info = fields.Nested(ServiceInfoResponsePayload, required=False)

    payload = fields.Nested(NextResponsePayload)


class PwAuthRequestSchema(IdPRequest):
    username = fields.Str(required=True)
    password = fields.Str(required=True)


class PwAuthResponseSchema(FluxStandardAction):
    class PwAuthResponsePayload(EduidSchema, CSRFResponseMixin):
        finished = fields.Bool(required=True)

    payload = fields.Nested(PwAuthResponsePayload)


class MfaAuthRequestSchema(IdPRequest):
    webauthn_response = fields.Dict(keys=fields.Str(), values=fields.Str(), default=None, required=False)


class MfaAuthResponseSchema(FluxStandardAction):
    class MfaAuthResponsePayload(EduidSchema, CSRFResponseMixin):
        finished = fields.Bool(required=True)
        webauthn_options = fields.Str(required=False)

    payload = fields.Nested(MfaAuthResponsePayload)


class TouRequestSchema(IdPRequest):
    versions = fields.Str(required=False, many=True)
    user_accepts = fields.Str(required=False)


class TouResponseSchema(FluxStandardAction):
    class TouResponsePayload(EduidSchema, CSRFResponseMixin):
        finished = fields.Bool(required=True)
        version = fields.Str(required=False)

    payload = fields.Nested(TouResponsePayload)


class UseOther1RequestSchema(IdPRequest):
    username = fields.Str(required=False)  # optional username, if the user supplies an e-mail address
    action = fields.Str(required=False)  # optional action, 'ABORT' or 'SUBMIT_CODE'
    response_code = fields.Str(required=False)  # optional response code, if action == 'SUBMIT_CODE'


class UseOther1ResponseSchema(FluxStandardAction):
    class UseOther1ResponsePayload(EduidSchema, CSRFResponseMixin):
        bad_attempts = fields.Int(required=True)  # number of incorrect response_code attempts
        expires_in = fields.Int(required=True)  # to use expires_at, the client clock have to be in sync with backend
        expires_max = fields.Int(required=True)  # to use expires_at, the client clock have to be in sync with backend
        qr_img = fields.Str(required=True)  # qr_url as an inline img
        qr_url = fields.Str(required=True)  # the link to where the user can manually enter short_code to proceed
        short_code = fields.Str(required=True)  # six-digit code for this request
        state = fields.Str(required=True)  # current state of request, an OtherDeviceState (NEW, PENDING etc.)
        state_id = fields.Str(required=True)  # database id for this state
        response_code_required = fields.Bool(required=True)  # True if a response code is required for this login
        # NOTE: It is CRITICAL to never return the response code to Device #1

    payload = fields.Nested(UseOther1ResponsePayload)


class UseOther2RequestSchema(EduidSchema, CSRFRequestMixin):
    action = fields.Str(required=False)  # optional action ('ABORT' is the only one on device 2)
    ref = fields.Str(missing=None, required=False)  # use login_ref on page reloads, when there is a pending_request
    # use state_id on first load from QR URL, before a pending_request is set up
    state_id = fields.Str(missing=None, required=False)


class UseOther2ResponseSchema(FluxStandardAction):
    class UseOther2ResponsePayload(EduidSchema, CSRFResponseMixin):
        class DeviceInfo(Schema):
            class ServiceInfo(Schema):
                display_name = fields.Dict(keys=fields.Str())

            addr = fields.Str(required=True)  # remote address of device1
            description = fields.Str(required=False)  # description of device1, based on User-Agent header
            proximity = fields.Str(required=True)  # how close the address of device1 is to the address of device2
            service_info = fields.Nested(ServiceInfo, required=False)
            is_known_device = fields.Boolean(required=True)

        device1_info = fields.Nested(DeviceInfo)
        expires_in = fields.Int(required=True)  # to use expires_at, the client clock have to be in sync with backend
        expires_max = fields.Int(required=True)  # to use expires_at, the client clock have to be in sync with backend
        login_ref = fields.Str(required=True)  # newly minted login_ref
        short_code = fields.Str(required=True)  # six-digit code for this request
        state = fields.Str(required=True)  # current state of request, an OtherDeviceState (NEW, PENDING etc.)
        response_code = fields.Str(
            required=False
        )  # the secret response code the user should enter on device 1 to get logged in
        response_code_required = fields.Bool(required=True)  # True if a response code is required for this login
        username = fields.Str(required=False)  # the username (e.g. e-mail address) of the user logging in
        display_name = fields.Str(required=False)  # the display_name of the user logging in

    payload = fields.Nested(UseOther2ResponsePayload)


class AbortRequestSchema(IdPRequest):
    pass


class AbortResponseSchema(FluxStandardAction):
    class AbortResponsePayload(EduidSchema, CSRFResponseMixin):
        finished = fields.Bool(required=True)

    payload = fields.Nested(AbortResponsePayload)


class NewDeviceRequestSchema(IdPRequest):
    pass


class NewDeviceResponseSchema(FluxStandardAction):
    class NewDeviceResponsePayload(EduidSchema, CSRFResponseMixin):
        new_device = fields.Str(required=True)

    payload = fields.Nested(NewDeviceResponsePayload)


class ErrorInfoResponseSchema(FluxStandardAction):
    class ErrorInfoResponsePayload(EduidSchema, CSRFResponseMixin):
        eppn = fields.Str(required=False)
        has_locked_nin = fields.Bool(required=False)
        has_verified_nin = fields.Bool(required=False)
        has_mfa = fields.Bool(required=False)
        logged_in = fields.Bool(required=True)

    payload = fields.Nested(ErrorInfoResponsePayload)
