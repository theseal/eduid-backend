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

from marshmallow import fields

from eduid.webapp.common.api.schemas.base import EduidSchema, FluxStandardAction
from eduid.webapp.common.api.schemas.csrf import CSRFRequestMixin, CSRFResponseMixin
from eduid.webapp.common.api.schemas.email import LowercaseEmail
from eduid.webapp.common.api.schemas.validators import validate_email
from eduid.webapp.email.validators import email_does_not_exist, email_exists

__author__ = "eperez"


class NoCSRFVerificationCodeSchema(EduidSchema):
    # Create the VerificationCodeSchema without forced CSRF token so it can be used for the GET verification view also
    code = fields.String(required=True)
    email = LowercaseEmail(required=True, validate=[validate_email, email_exists])


class VerificationCodeSchema(NoCSRFVerificationCodeSchema, CSRFRequestMixin):
    pass


class EmailSchema(EduidSchema, CSRFRequestMixin):

    email = LowercaseEmail(required=True, validate=validate_email)
    verified = fields.Boolean(attribute="verified")
    primary = fields.Boolean(attribute="primary")


class AddEmailSchema(EmailSchema):

    email = LowercaseEmail(required=True, validate=[validate_email, email_does_not_exist])


class ChangeEmailSchema(EduidSchema, CSRFRequestMixin):

    email = LowercaseEmail(required=True, validate=[validate_email, email_exists])


class EmailListPayload(EduidSchema, CSRFRequestMixin, CSRFResponseMixin):

    emails = fields.Nested(EmailSchema, many=True)


class EmailResponseSchema(FluxStandardAction):

    payload = fields.Nested(EmailListPayload)
