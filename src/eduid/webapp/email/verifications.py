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

from flask import current_app, render_template, url_for
from flask_babel import gettext as _

from eduid.userdb import User
from eduid.userdb.logs import MailAddressProofing
from eduid.userdb.mail import MailAddress
from eduid.userdb.proofing import EmailProofingElement, EmailProofingState
from eduid.webapp.common.api.utils import get_unique_hash, save_and_sync_user


def new_proofing_state(email: str, user: User):
    old_state = current_app.proofing_statedb.get_state_by_eppn_and_email(user.eppn, email)

    if old_state is not None:
        if old_state.is_throttled(current_app.conf.throttle_resend_seconds):
            return None
        current_app.proofing_statedb.remove_state(old_state)
        current_app.logger.info("Removed old proofing state")
        current_app.logger.debug("Old proofing state: {}".format(old_state.to_dict()))

    verification = EmailProofingElement(email=email, verification_code=get_unique_hash(), created_by="email")
    proofing_state = EmailProofingState(id=None, modified_ts=None, eppn=user.eppn, verification=verification)
    # XXX This should be an atomic transaction together with saving
    # the user and sending the letter.
    current_app.proofing_statedb.save(proofing_state)

    current_app.logger.info("Created new email proofing state")
    current_app.logger.debug("Proofing state: {!r}.".format(proofing_state.to_dict()))

    return proofing_state


def send_verification_code(email: str, user: User) -> bool:
    subject = _("eduID confirmation email")
    state = new_proofing_state(email, user)
    if state is None:
        return False

    link = url_for("email.verify_link", code=state.verification.verification_code, email=email, _external=True)
    site_name = current_app.conf.eduid_site_name
    site_url = current_app.conf.eduid_site_url

    context = {
        "email": email,
        "verification_link": link,
        "site_url": site_url,
        "site_name": site_name,
        "code": state.verification.verification_code,
    }

    text = render_template("verification_email.txt.jinja2", **context)
    html = render_template("verification_email.html.jinja2", **context)

    current_app.mail_relay.sendmail(subject, [email], text, html, reference=state.reference)
    current_app.logger.info(
        "Sent email address verification mail to user {}" " about address {!s}.".format(user, email)
    )
    return True


def verify_mail_address(state, proofing_user):
    """
    :param proofing_user: ProofingUser
    :param state: E-mail proofing state

    :type proofing_user: eduid.userdb.proofing.ProofingUser
    :type state: EmailProofingState

    :return: None

    """
    email = proofing_user.mail_addresses.find(state.verification.email)
    if not email:
        email = MailAddress(email=state.verification.email, created_by="email", is_verified=True, is_primary=False)
        proofing_user.mail_addresses.add(email)
        # Adding the phone to the list creates a copy of the element, so we have to 'find' it again
        email = proofing_user.mail_addresses.find(state.verification.email)

    email.is_verified = True
    if not proofing_user.mail_addresses.primary:
        email.is_primary = True

    mail_address_proofing = MailAddressProofing(
        eppn=proofing_user.eppn,
        created_by="email",
        mail_address=email.email,
        reference=state.reference,
        proofing_version="2013v1",
    )
    if current_app.proofing_log.save(mail_address_proofing):
        save_and_sync_user(proofing_user)
        current_app.logger.info(f"Email address {repr(state.verification.email)} confirmed for user {proofing_user}")
        current_app.stats.count(name="email_verify_success", value=1)
        current_app.proofing_statedb.remove_state(state)
        current_app.logger.debug(f"Removed proofing state: {state}")
