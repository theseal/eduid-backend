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
from typing import Optional

from flask import Blueprint

from eduid.userdb import User
from eduid.userdb.exceptions import UserOutOfSync
from eduid.userdb.personal_data import PersonalDataUser
from eduid.webapp.common.api.decorators import MarshalWith, UnmarshalWith, require_user
from eduid.webapp.common.api.messages import CommonMsg, FluxData, error_response, success_response
from eduid.webapp.common.api.utils import save_and_sync_user
from eduid.webapp.personal_data.app import current_pdata_app as current_app
from eduid.webapp.personal_data.helpers import PDataMsg
from eduid.webapp.personal_data.schemas import (
    AllDataResponseSchema,
    IdentitiesResponseSchema,
    PersonalDataRequestSchema,
    PersonalDataResponseSchema,
)

pd_views = Blueprint("personal_data", __name__, url_prefix="")


@pd_views.route("/all-user-data", methods=["GET"])
@MarshalWith(AllDataResponseSchema)
@require_user
def get_all_data(user: User) -> FluxData:
    user_dict = user.to_dict()
    user_dict["identities"] = user.identities.to_frontend_format()
    # TODO: remove nins after frontend stops using it
    user_dict["nins"] = []
    if user.identities.nin is not None:
        user_dict["nins"].append(user.identities.nin.to_old_nin())
    return success_response(payload=user_dict)


@pd_views.route("/user", methods=["GET"])
@MarshalWith(PersonalDataResponseSchema)
@require_user
def get_user(user: User) -> FluxData:
    return success_response(payload=user.to_dict())


@pd_views.route("/user", methods=["POST"])
@UnmarshalWith(PersonalDataRequestSchema)
@MarshalWith(PersonalDataResponseSchema)
@require_user
def post_user(user: User, given_name: str, surname: str, language: str, display_name: Optional[str] = None) -> FluxData:
    # TODO: Remove display_name when frontend stops sending it
    personal_data_user = PersonalDataUser.from_user(user, current_app.private_userdb)
    current_app.logger.debug("Trying to save user {}".format(user))

    # disallow change of first name, surname and display name if the user is verified
    if not user.identities.is_verified:
        personal_data_user.given_name = given_name
        personal_data_user.surname = surname
        personal_data_user.display_name = f"{given_name} {surname}"
    personal_data_user.language = language
    try:
        save_and_sync_user(personal_data_user)
    except UserOutOfSync:
        return error_response(message=CommonMsg.out_of_sync)
    current_app.stats.count(name="personal_data_saved", value=1)
    current_app.logger.info("Saved personal data for user {}".format(personal_data_user))

    personal_data = personal_data_user.to_dict()
    return success_response(payload=personal_data, message=PDataMsg.save_success)


@pd_views.route("/nins", methods=["GET"])
@MarshalWith(IdentitiesResponseSchema)
@require_user
def get_nins(user) -> FluxData:
    # TODO: remove endpoint after frontend stops using it
    return get_identities()


@pd_views.route("/identities", methods=["GET"])
@MarshalWith(IdentitiesResponseSchema)
@require_user
def get_identities(user) -> FluxData:
    # TODO: remove nins after frontend stops using it
    data = {"identities": user.identities.to_frontend_format(), "nins": []}

    if user.identities.nin is not None:
        data["nins"].append(user.identities.nin.to_old_nin())

    return success_response(payload=data)
