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
Here it is described the behaviour expected from a front side app that uses this
service. Just the main, success path will be described; to cover paths
taken due to error conditions, check the docstrings for each method, below.

We assume that this front side app is a login app that is already loaded in the
end user's browser, and which offers a "reset password" link side by side with
inputs for credentials.

When this "reset password" link is followed, the user will be presented a form,
with a text input for an email address and a "send" button. The user enters
(one of) her email(s) and submits the form, which results in a POST to the
init_reset_pw view (at /), with the email as only data.

The result of calling this init_reset_pw method will be the generation of a
password reset state in a db, keyed by a hash code, and the sending of an email
with a link that includes the mentioned hash code.

When the user follows the link in the email, the front app will load, it will
grab the code from document.location.href, and will use it to send a POST to
the config_reset_pw view located at /config/, with the code as only data. This
POST will return the same code, a suggested password, and an array of (masked)
verified phone numbers.

Now there are 2 possibilities.

The first happens when the user has no verified phone numbers. Then she will be
shown a form where she can choose the suggested password or enter a custom one,
submit it to the set_new_pw view at /new-password/, and have her password
reset as a result. In this case, with no extra security, all her verified phone
numbers and NINs will be unverified.

The second possibility is that the user had some phone number(s) verified. Then
she will be presented with a choice, to either use extra security, or not. If
she chooses not to use extra security, the workflow will continue as with the
first possibility.

If the user chooses extra security (clicking on a particular verified phone number),
an SMS with a new code will be sent to the chosen phone number, and the
user will be presented with the same form as in the first possibility,
supplemented with a text input for the SMS'ed code. In this case submitting the
form will also result in resetting her password, but without unverifying any of
her data.
"""
import json
import time

from flask import Blueprint, request

from eduid_common.api.decorators import MarshalWith, UnmarshalWith
from eduid_common.api.exceptions import MsgTaskFailed
from eduid_common.api.schemas.base import FluxStandardAction
from eduid_common.authn import fido_tokens
from eduid_common.session import session
from eduid_userdb.reset_password import ResetPasswordEmailAndPhoneState

from eduid_webapp.reset_password.app import current_reset_password_app as current_app
from eduid_webapp.reset_password.helpers import (
    BadCode,
    ResetPwMsg,
    check_password,
    error_message,
    generate_suggested_password,
    get_extra_security_alternatives,
    get_pwreset_state,
    hash_password,
    mask_alternatives,
    reset_user_password,
    send_password_reset_mail,
    send_verify_phone_code,
    success_message,
    verify_email_address,
    verify_phone_number,
)
from eduid_webapp.reset_password.schemas import (
    ResetPasswordEmailCodeSchema,
    ResetPasswordExtraSecPhoneSchema,
    ResetPasswordInitSchema,
    ResetPasswordWithCodeSchema,
    ResetPasswordWithPhoneCodeSchema,
    ResetPasswordWithSecTokenSchema,
)
from eduid_webapp.security.helpers import get_zxcvbn_terms

SESSION_PREFIX = "eduid_webapp.reset_password.views"


reset_password_views = Blueprint('reset_password', __name__, url_prefix='/reset', template_folder='templates')


@reset_password_views.route('/', methods=['POST'])
@UnmarshalWith(ResetPasswordInitSchema)
@MarshalWith(FluxStandardAction)
def init_reset_pw(email: str) -> dict:
    """
    View that receives an email address to initiate a reset password process.
    It returns a message informing of the result of the operation.

    Preconditions required for the call to succeed:
    * There is a valid user corresponding to the received email address.

    As side effects, this view will:
    * Create a PasswordResetEmailState in the password_reset_state_db
      (holding the email address, the eppn of the user associated to the
      email address in the central userdb, and a freshly generated random hash
      as an identifier code for the created state);
    * Email the generated code to the received email address.

    The operation can fail due to:
    * The email address does not correspond to any valid user in the central db;
    * There is some problem sending the email.
    """
    current_app.logger.info(f'Trying to send password reset email to {email}')
    try:
        send_password_reset_mail(email)
    except BadCode as error:
        current_app.logger.error(f'Sending password reset e-mail for {email} failed: {error}')
        return error_message(error.msg)

    return success_message(ResetPwMsg.send_pw_success)


@reset_password_views.route('/config/', methods=['POST'])
@UnmarshalWith(ResetPasswordEmailCodeSchema)
@MarshalWith(FluxStandardAction)
def config_reset_pw(code: str) -> dict:
    """
    View that receives an emailed reset password code and returns the
    configuration needed for the reset password form.

    Preconditions required for the call to succeed:
    * A PasswordResetEmailState object in the password_reset_state_db
      keyed by the received code.

    The configuration returned (in case of success) will include:
    * The received code;
    * A newly generated suggested password;
    * In case the user corresponding to the email address has verified phone
      numbers, these will be sent (masked) to allow the user to use extra
      security. (If the user does not use extra security, any verified NIN or
      phone number will be unverified upon resetting the password).

    As side effects, this view will:
    * Create a MailAddressProofing element in the proofing_log;
    * Set the email_code.is_verified flag in the PasswordResetEmailState
      object;
    * Set a hash of the generated password in the session.

    This operation may fail due to:
    * The code does not correspond to a valid state in the db;
    * The code has expired;
    * No valid user corresponds to the eppn stored in the state.
    """
    current_app.logger.info(f'Configuring password reset form for {code}')
    try:
        state = get_pwreset_state(code)
    except BadCode as e:
        return error_message(e.msg)

    verify_email_address(state)

    new_password = generate_suggested_password()
    session.reset_password.generated_password_hash = hash_password(new_password)

    user = current_app.central_userdb.get_user_by_eppn(state.eppn)
    alternatives = get_extra_security_alternatives(user, SESSION_PREFIX)
    state.extra_security = alternatives
    current_app.password_reset_state_db.save(state)

    return {
        'csrf_token': session.get_csrf_token(),
        'suggested_password': new_password,
        'email_code': state.email_code.code,
        'email_address': state.email_address,
        'extra_security': mask_alternatives(alternatives),
        'password_entropy': current_app.config.password_entropy,
        'password_length': current_app.config.password_length,
        'password_service_url': current_app.config.password_service_url,
        'zxcvbn_terms': get_zxcvbn_terms(state.eppn),
    }


class BadStateOrData(Exception):
    def __init__(self, msg):
        self.msg = msg


def _get_state_and_data(SchemaClass):

    if not request.data:
        raise BadStateOrData(ResetPwMsg.chpass_no_data)

    data = json.loads(request.data)

    if 'code' not in data:
        raise BadStateOrData(ResetPwMsg.state_no_key)

    code = data['code']
    try:
        state = get_pwreset_state(code)
    except BadCode as e:
        raise BadStateOrData(e.msg)

    resetpw_user = current_app.central_userdb.get_user_by_eppn(state.eppn)
    min_entropy = current_app.config.password_entropy

    schema = SchemaClass(zxcvbn_terms=get_zxcvbn_terms(resetpw_user.eppn), min_entropy=int(min_entropy))

    form = schema.load(json.loads(request.data))
    current_app.logger.debug(f"Reset password data: {form}")
    if form.errors:
        if 'csrf_token' in form.errors:
            raise BadStateOrData(ResetPwMsg.csrf_missing)
        raise BadStateOrData(ResetPwMsg.chpass_weak)

    if session.get_csrf_token() != form.data['csrf_token']:
        raise BadStateOrData(ResetPwMsg.csrf_try_again)

    return (resetpw_user, state, form.data)


@reset_password_views.route('/new-password/', methods=['POST'])
@MarshalWith(FluxStandardAction)
def set_new_pw() -> dict:
    """
    View that receives an emailed reset password code and a password, and sets
    the password as credential for the user, with no extra security.

    Preconditions required for the call to succeed:
    * A PasswordResetEmailState object in the password_reset_state_db
      keyed by the received code.
    * A flag in said state object indicating that the emailed code has already
      been verifed.

    As side effects, this view will:
    * Compare the received password with the hash in the session to mark
      it accordingly (as suggested or as custom);
    * Revoke all password credentials the user had;
    * Unverify any verified phone number or NIN the user previously had.

    This operation may fail due to:
    * The code does not correspond to a valid state in the db;
    * The code has expired;
    * No valid user corresponds to the eppn stored in the state;
    * Communication problems with the VCCS backend;
    * Synchronization problems with the central user db.
    """
    try:
        resetpw_user, state, data = _get_state_and_data(ResetPasswordWithCodeSchema)
    except BadStateOrData as e:
        return error_message(e.msg)

    password = data.get('password')

    hashed = session.reset_password.generated_password_hash
    if check_password(password, hashed):
        state.generated_password = True
        current_app.logger.info('Generated password used')
        current_app.stats.count(name='reset_password_generated_password_used')
    else:
        state.generated_password = False
        current_app.logger.info('Custom password used')
        current_app.stats.count(name='reset_password_custom_password_used')

    current_app.logger.info(f'Resetting password for user {resetpw_user}')
    reset_user_password(resetpw_user, state, password)
    current_app.logger.info(f'Password reset done, removing state for {resetpw_user}')
    current_app.password_reset_state_db.remove_state(state)
    return success_message(ResetPwMsg.pw_resetted)


@reset_password_views.route('/extra-security-phone/', methods=['POST'])
@UnmarshalWith(ResetPasswordExtraSecPhoneSchema)
@MarshalWith(FluxStandardAction)
def choose_extra_security_phone(code: str, phone_index: int) -> dict:
    """
    View called when the user chooses extra security (she can do that when she
    has some verified phone number). It receives an emailed reset password code
    and an index for one of the verified phone numbers, and returns info on the
    result of the attempted operation.

    Preconditions required for the call to succeed:
    * A PasswordResetEmailState object in the password_reset_state_db
      keyed by the received code.
    * A flag in said state object indicating that the emailed code has already
      been verifed.
    * The user referenced in the state has at least phone_index (number) of
      verified phone numbers.

    As side effects, this operation will:
    * Copy the data in the PasswordResetEmailState to a new
      PasswordResetEmailAndPhoneState;
    * Create a new random hash as identifier code for the new state;
    * Store this code in the new state;
    * Send an SMS message with the code to the phone number corresponding to
      the received phone_index;

    This operation may fail due to:
    * The code does not correspond to a valid state in the db;
    * The code has expired;
    * No valid user corresponds to the eppn stored in the state;
    * Problems sending the SMS message
    """
    try:
        state = get_pwreset_state(code)
    except BadCode as e:
        return error_message(e.msg)

    if isinstance(state, ResetPasswordEmailAndPhoneState):
        now = int(time.time())
        if int(state.modified_ts.timestamp()) > now - current_app.config.throttle_sms_seconds:
            current_app.logger.info(f'Throttling reset password SMSs for: {state.eppn}')
            return error_message(ResetPwMsg.send_sms_throttled)

    current_app.logger.info(f'Password reset: choose_extra_security for ' f'user with eppn {state.eppn}')

    # Check that the email code has been validated
    if not state.email_code.is_verified:
        current_app.logger.info(f'User with eppn {state.eppn} has not ' f'verified their email address')
        return error_message(ResetPwMsg.email_not_validated)

    phone_number = state.extra_security['phone_numbers'][phone_index]
    current_app.logger.info(f'Trying to send password reset sms to user with ' f'eppn {state.eppn}')
    try:
        send_verify_phone_code(state, phone_number["number"])
    except MsgTaskFailed as e:
        current_app.logger.error(f'Sending sms failed: {e}')
        return error_message(ResetPwMsg.send_sms_failure)

    current_app.stats.count(name='reset_password_extra_security_phone')
    return success_message(ResetPwMsg.send_sms_success)


@reset_password_views.route('/new-password-secure-phone/', methods=['POST'])
@MarshalWith(FluxStandardAction)
def set_new_pw_extra_security_phone() -> dict:
    """
    View that receives an emailed reset password code, an SMS'ed reset password
    code, and a password, and sets the password as credential for the user, with
    extra security.

    Preconditions required for the call to succeed:
    * A PasswordResetEmailAndPhoneState object in the password_reset_state_db
      keyed by the received codes.
    * A flag in said state object indicating that the emailed code has already
      been verifed.

    As side effects, this view will:
    * Compare the received password with the hash in the session to mark
      it accordingly (as suggested or as custom);
    * Revoke all password credentials the user had;

    This operation may fail due to:
    * The codes do not correspond to a valid state in the db;
    * Any of the codes have expired;
    * No valid user corresponds to the eppn stored in the state;
    * Communication problems with the VCCS backend;
    * Synchronization problems with the central user db.
    """
    try:
        resetpw_user, state, data = _get_state_and_data(ResetPasswordWithPhoneCodeSchema)
    except BadStateOrData as e:
        return error_message(e.msg)

    password = data.get('password')
    phone_code = data.get('phone_code')

    # Backdoor for the staging and dev environments where a magic code
    # bypasses verification of the sms'ed code, to be used in automated integration tests.
    # here we store the real code in the session,
    # to recover it in case the user sends the magic code.
    if current_app.config.environment in ('staging', 'dev') and current_app.config.magic_code:
        if phone_code == current_app.config.magic_code:
            current_app.logger.info('Using BACKDOOR to bypass verification of SMS code!')
            phone_code = session.reset_password.resetpw_sms_verification_code

    if phone_code == state.phone_code.code:
        if not verify_phone_number(state):
            current_app.logger.info(f'Could not verify phone code for {state.eppn}')
            return error_message(ResetPwMsg.phone_invalid)

        current_app.logger.info(f'Phone code verified for {state.eppn}')
        current_app.stats.count(name='reset_password_extra_security_phone_success')
    else:
        current_app.logger.info(f'Could not verify phone code for {state.eppn}')
        return error_message(ResetPwMsg.unkown_phone_code)

    hashed = session.reset_password.generated_password_hash
    if check_password(password, hashed):
        state.generated_password = True
        current_app.logger.info('Generated password used')
        current_app.stats.count(name='reset_password_generated_password_used')
    else:
        state.generated_password = False
        current_app.logger.info('Custom password used')
        current_app.stats.count(name='reset_password_custom_password_used')

    user = current_app.central_userdb.get_user_by_eppn(state.eppn, raise_on_missing=False)

    current_app.logger.info(f'Resetting password for user {user}')
    reset_user_password(user, state, password)
    current_app.logger.info(f'Password reset done, removing state for {user}')
    current_app.password_reset_state_db.remove_state(state)
    return success_message(ResetPwMsg.pw_resetted)


@reset_password_views.route('/new-password-secure-token/', methods=['POST'])
@MarshalWith(FluxStandardAction)
def set_new_pw_extra_security_token() -> dict:
    """
    View that receives an emailed reset password code, hw token data,
    and a password, and sets the password as credential for the user, with
    extra security.

    Preconditions required for the call to succeed:
    * A PasswordResetEmailAndTokenState object in the password_reset_state_db
      keyed by the received code.
    * A flag in said state object indicating that the emailed code has already
      been verifed.

    As side effects, this view will:
    * Compare the received password with the hash in the session to mark
      it accordingly (as suggested or as custom);
    * Revoke all password credentials the user had;

    This operation may fail due to:
    * The codes do not correspond to a valid state in the db;
    * Any of the codes have expired;
    * No valid user corresponds to the eppn stored in the state;
    * Communication problems with the VCCS backend;
    * Synchronization problems with the central user db.
    """
    try:
        resetpw_user, state, data = _get_state_and_data(ResetPasswordWithSecTokenSchema)
    except BadStateOrData as e:
        return error_message(e.msg)

    password = data.get('password')

    req_json = request.get_json()
    if not req_json:
        current_app.logger.error(f'No data in request to authn {state.eppn}')
        return error_message(ResetPwMsg.mfa_no_data)

    hashed = session.reset_password.generated_password_hash
    if check_password(password, hashed):
        state.generated_password = True
        current_app.logger.info('Generated password used')
        current_app.stats.count(name='reset_password_generated_password_used')
    else:
        state.generated_password = False
        current_app.logger.info('Custom password used')
        current_app.stats.count(name='reset_password_custom_password_used')

    user = current_app.central_userdb.get_user_by_eppn(state.eppn, raise_on_missing=False)

    # Process POSTed data
    success = False
    if 'tokenResponse' in req_json:
        # CTAP1/U2F
        token_response = request.get_json().get('tokenResponse', '')
        current_app.logger.debug(f'U2F token response: {token_response}')

        challenge = session.get(SESSION_PREFIX + '.u2f.challenge')
        current_app.logger.debug(f'Challenge: {challenge}')

        result = fido_tokens.verify_u2f(user, challenge, token_response)

        if result is not None:
            success = result['success']

    elif not success and 'authenticatorData' in req_json:
        # CTAP2/Webauthn
        try:
            result = fido_tokens.verify_webauthn(user, req_json, SESSION_PREFIX)
        except fido_tokens.VerificationProblem:
            pass
        else:
            success = result['success']

    else:
        current_app.logger.error(f'Neither U2F nor Webauthn data in request to authn {user}')
        current_app.logger.debug(f'Request: {req_json}')

    if success:
        current_app.logger.info(f'Resetting password for user {user}')
        reset_user_password(user, state, password)
        current_app.logger.info(f'Password reset done, removing state for {user}')
        current_app.password_reset_state_db.remove_state(state)
        return success_message(ResetPwMsg.pw_resetted)

    return error_message(ResetPwMsg.fido_token_fail)
