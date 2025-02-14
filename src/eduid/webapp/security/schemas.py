# -*- coding: utf-8 -*-
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


from marshmallow import ValidationError, fields, validates

from eduid.webapp.common.api.schemas.base import EduidSchema, FluxStandardAction
from eduid.webapp.common.api.schemas.csrf import CSRFRequestMixin, CSRFResponseMixin
from eduid.webapp.common.api.schemas.identity import IdentitiesSchema, NinSchema
from eduid.webapp.common.api.schemas.password import PasswordSchema
from eduid.webapp.common.api.schemas.validators import validate_nin


class CredentialSchema(EduidSchema):
    key = fields.String(required=True)
    credential_type = fields.String(required=True)
    created_ts = fields.String(required=True)
    success_ts = fields.String(required=True)
    used_for_login = fields.Boolean(required=True, default=False)
    verified = fields.Boolean(required=True, default=False)
    description = fields.String(required=False)


class CredentialList(EduidSchema, CSRFResponseMixin):
    credentials = fields.Nested(CredentialSchema, many=True)


class SecurityResponseSchema(FluxStandardAction):
    payload = fields.Nested(CredentialList)


class ChpassResponseSchema(SecurityResponseSchema):
    class ChpassResponsePayload(CredentialList):
        next_url = fields.String(required=True)

    payload = fields.Nested(ChpassResponsePayload)


class ChangePasswordRequestSchema(EduidSchema, CSRFRequestMixin):

    old_password = fields.String(required=False)
    new_password = fields.String(required=True)


class RedirectResponseSchema(FluxStandardAction):
    class RedirectPayload(EduidSchema, CSRFResponseMixin):
        location = fields.String(required=True)

    payload = fields.Nested(RedirectPayload, many=False)


class SuggestedPasswordResponseSchema(FluxStandardAction):
    class SuggestedPasswordPayload(EduidSchema, CSRFResponseMixin):
        suggested_password = fields.String(required=True)

    payload = fields.Nested(SuggestedPasswordPayload, many=False)


# TODO: Remove this when frontend for new change password view exist
class ChangePasswordSchema(PasswordSchema):

    csrf_token = fields.String(required=True)
    old_password = fields.String(required=True)
    new_password = fields.String(required=True)

    @validates("new_password")
    def validate_custom_password(self, value, **kwargs):
        # Set a new error message
        try:
            self.validate_password(value)
        except ValidationError:
            raise ValidationError("chpass.weak-pass")


class AccountTerminatedSchema(FluxStandardAction):
    pass


# webauthn schemas
class WebauthnOptionsResponseSchema(FluxStandardAction):
    class WebauthnOptionsResponsePayload(EduidSchema, CSRFResponseMixin):
        options = fields.String(required=True)

    payload = fields.Nested(WebauthnOptionsResponsePayload)


class WebauthnRegisterBeginSchema(EduidSchema, CSRFRequestMixin):

    authenticator = fields.String(required=True)


class WebauthnRegisterRequestSchema(EduidSchema, CSRFRequestMixin):

    credential_id = fields.String(required=True, data_key="credentialId")
    attestation_object = fields.String(required=True, data_key="attestationObject")
    client_data = fields.String(required=True, data_key="clientDataJSON")
    description = fields.String(required=True)


class RemoveWebauthnTokenRequestSchema(EduidSchema, CSRFRequestMixin):

    credential_key = fields.String(required=True)


class VerifyWithWebauthnTokenRequestSchema(EduidSchema):
    key_handle = fields.String(required=True, data_key="keyHandle")
    signature_data = fields.String(required=True, data_key="signatureData")
    client_data = fields.String(required=True, data_key="clientData")


class VerifyWithWebauthnTokenResponseSchema(FluxStandardAction):
    class Payload(CSRFResponseMixin):
        key_handle = fields.String(required=True, data_key="keyHandle")
        signature_data = fields.String(required=True, data_key="signatureData")
        client_data = fields.String(required=True, data_key="clientData")

    payload = fields.Nested(Payload)


# NIN schemas
class NINRequestSchema(EduidSchema, CSRFRequestMixin):

    nin = fields.String(required=True, validate=validate_nin)


class IdentitiesResponseSchema(FluxStandardAction):
    class RemoveNINPayload(EduidSchema, CSRFResponseMixin):
        message = fields.String(required=False)
        nins = fields.Nested(NinSchema, many=True)
        identities = fields.Nested(IdentitiesSchema)

    payload = fields.Nested(RemoveNINPayload)


class UserUpdateResponseSchema(FluxStandardAction):
    class UserUpdatePayload(EduidSchema, CSRFRequestMixin):
        given_name = fields.String(attribute="givenName")
        surname = fields.String()

    payload = fields.Nested(UserUpdatePayload)
