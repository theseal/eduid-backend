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
import math
import os
from typing import Union, Optional, List
from enum import Enum, unique

import bcrypt
from flask import url_for
from flask import render_template
from flask_babel import gettext as _

from eduid_userdb.exceptions import UserHasNotCompletedSignup
from eduid_userdb.exceptions import DocumentDoesNotExist
from eduid_userdb.reset_password import ResetPasswordUser
from eduid_userdb.reset_password import ResetPasswordState
from eduid_userdb.reset_password import ResetPasswordEmailState
from eduid_userdb.reset_password import ResetPasswordEmailAndPhoneState
from eduid_userdb.logs import MailAddressProofing
from eduid_userdb.logs import PhoneNumberProofing
from eduid_common.api.exceptions import MailTaskFailed
from eduid_common.api.utils import save_and_sync_user
from eduid_common.api.utils import get_unique_hash
from eduid_common.api.utils import get_short_hash
from eduid_common.api.helpers import send_mail
from eduid_common.authn.utils import generate_password
from eduid_common.authn.vccs import reset_password
from eduid_webapp.reset_password.app import current_reset_password_app as current_app


@unique
class Msg(Enum):
    """
    Messages sent to the front end with information on the results of the
    attempted operations on the back end.
    """
    # The user has sent a code that corresponds to no known password reset
    # request
    unknown_code = 'resetpw.unknown-code'
    # The user has sent an SMS'ed code that corresponds to no known password
    # reset request
    unkown_phone_code = 'resetpw.phone-code-unknown'
    # The user has sent a code that has expired
    expired_email_code = 'resetpw.expired-email-code'
    # The user has sent an SMS'ed code that has expired
    expired_sms_code = 'resetpw.expired-sms-code'
    # There was some problem sending the email with the code.
    send_pw_failure = 'resetpw.send-pw-fail'
    # A new code has been generated and sent by email successfully
    send_pw_success = 'resetpw.send-pw-success'
    # The password has been successfully resetted
    pw_resetted = 'resetpw.pw-resetted'
    # There was some problem sending the SMS with the (extra security) code.
    send_sms_failure = 'resetpw.sms-failed'
    # A new (extra security) code has been generated and sent by SMS
    # successfully
    send_sms_success = 'resetpw.sms-success'
    # The phone number has not been verified. Should not happen.
    phone_invalid = 'resetpw.phone-invalid'
    # No user was found corresponding to the password reset state. Should not
    # happen.
    user_not_found = 'resetpw.user-not-found'
    # The email address has not been verified. Should not happen.
    email_not_validated = 'resetpw.email-not-validated'
    #
    invalid_user = 'resetpw.incomplete-user'



class BadCode(Exception):
    """
    Exception to signal that the password reset code received is not valid.
    """
    def __init__(self, msg: str):
        self.msg = msg


def success_message(message: Msg) -> dict:
    return {
        '_status': 'ok',
        'message': str(message.value)
    }


def error_message(message: Msg) -> dict:
    return {
        '_status': 'error',
        'message': str(message.value)
    }


def get_pwreset_state(email_code: str) -> ResetPasswordState:
    """
    get the password reset state for the provided code

    raises BadCode in case of problems
    """
    mail_expiration_time = current_app.config.email_code_timeout
    sms_expiration_time = current_app.config.phone_code_timeout
    try:
        state = current_app.password_reset_state_db.get_state_by_email_code(email_code)
        current_app.logger.debug(f'Found state using email_code {email_code}: {state}')
    except DocumentDoesNotExist:
        current_app.logger.info(f'State not found: {email_code}')
        raise BadCode(Msg.unknown_code)

    if state.email_code.is_expired(mail_expiration_time):
        current_app.logger.info(f'State expired: {email_code}')
        raise BadCode(Msg.expired_email_code)

    if isinstance(state, ResetPasswordEmailAndPhoneState) and state.phone_code.is_expired(sms_expiration_time):
        current_app.logger.info(f'Phone code expired for state: {email_code}')
        # Revert the state to EmailState to allow the user to choose extra security again
        current_app.password_reset_state_db.remove_state(state)
        state = ResetPasswordEmailState(eppn=state.eppn, email_address=state.email_address,
                                        email_code=state.email_code)
        current_app.password_reset_state_db.save(state)
        raise BadCode(Msg.expired_sms_code)

    return state


def send_password_reset_mail(email_address: str):
    """
    :param email_address: User input for password reset
    """
    try:
        user = current_app.central_userdb.get_user_by_mail(email_address)
    except UserHasNotCompletedSignup:
        # Old bug where incomplete signup users where written to the central db
        current_app.logger.info(f"Cannot reset a password with the following "
                                f"email address: {email_address}: incomplete user")
        raise BadCode(Msg.invalid_user)
    except DocumentDoesNotExist:
        current_app.logger.info(f"Cannot reset a password with the following "
                                f"unknown email address: {email_address}.")
        raise BadCode(Msg.user_not_found)

    state = ResetPasswordEmailState(eppn=user.eppn,
                                    email_address=email_address,
                                    email_code=get_unique_hash())
    current_app.password_reset_state_db.save(state)
    text_template = 'reset_password_email.txt.jinja2'
    html_template = 'reset_password_email.html.jinja2'
    to_addresses = [address.email for address in user.mail_addresses.verified.to_list()]

    pwreset_timeout = current_app.config.email_code_timeout // 60 // 60  # seconds to hours
    context = {
        'reset_password_link': url_for('reset_password.set_new_pw',
                                       email_code=state.email_code.code,
                                       _external=True),
        'password_reset_timeout': pwreset_timeout
    }
    subject = _('Reset password')
    try:
        send_mail(subject, to_addresses, text_template,
                  html_template, current_app, context, state.reference)
    except MailTaskFailed as error:
        current_app.logger.error(f'Sending password reset e-mail for {email} failed: {error}')
        raise BadCode(Msg.send_pw_failure)

    current_app.logger.info(f'Sent password reset email to user {user}')
    current_app.logger.debug(f'Mail addresses: {to_addresses}')


def generate_suggested_password() -> str:
    """
    The suggested password is hashed and saved in session to avoid form hijacking
    """
    password_length = current_app.config.password_length

    password = generate_password(length=password_length)
    password = ' '.join([password[i*4: i*4+4] for i in range(0, math.ceil(len(password)/4))])

    return password


def hash_password(password: str, salt: str,
                  strip_whitespace: bool = True) -> bytes:
    """
    :param password: password as plaintext
    :param salt: NDNv1H1 salt to be used for pre-hashing
    :param strip_whitespace: Whether to remove all whitespace from input
    """

    if not salt.startswith('$NDNv1H1$'):
        raise ValueError('Invalid salt (not NDNv1H1)')

    salt, key_length, rounds = decode_salt(salt)

    if strip_whitespace:
        password = ''.join(password.split())

    T1 = bytes(f"{len(password)}{password}", 'utf-8')

    return bcrypt.kdf(T1, salt, key_length, rounds)


def generate_salt() -> str:
    """
    Function to generate a NDNv1H1 salt.
    """
    salt_length = current_app.config.password_salt_length
    key_length = current_app.config.password_hash_length
    rounds = current_app.config.password_generation_rounds
    random = os.urandom(salt_length)
    random_str = random.hex()
    return f"$NDNv1H1${random_str}${key_length}${rounds}$"


def decode_salt(salt: str):
    """
    Function to decode a NDNv1H1 salt.
    """
    _, version, salt, desired_key_length, rounds, _ = salt.split('$')
    if version == 'NDNv1H1':
        bsalt = bytes().fromhex(salt)
        return bsalt, int(desired_key_length), int(rounds)
    raise NotImplementedError('Unknown hashing scheme')


def extra_security_used(state: ResetPasswordState) -> bool:
    """
    Check if any extra security method was used

    :param state: Password reset state
    :type state: ResetPasswordState
    :return: True|False
    :rtype: bool
    """
    if isinstance(state, ResetPasswordEmailAndPhoneState):
        return state.email_code.is_verified and state.phone_code.is_verified

    return False


def reset_user_password(state: ResetPasswordState, password: str):
    """
    :param state: Password reset state
    :param password: Plain text password
    """
    vccs_url = current_app.config.vccs_url

    user = current_app.central_userdb.get_user_by_eppn(state.eppn, raise_on_missing=False)
    reset_password_user = ResetPasswordUser.from_user(user, private_userdb=current_app.private_userdb)

    # If no extra security is all verified information (except email addresses) is set to not verified
    if not extra_security_used(state):
        current_app.logger.info(f'No extra security used by user {state.eppn}')
        # Phone numbers
        verified_phone_numbers = reset_password_user.phone_numbers.verified.to_list()
        if verified_phone_numbers:
            current_app.logger.info(f'Unverifying phone numbers for user {state.eppn}')
            reset_password_user.phone_numbers.primary.is_primary = False
            for phone_number in verified_phone_numbers:
                phone_number.is_verified = False
                current_app.logger.debug(f'Phone number {phone_number.number} unverified')
        # NINs
        verified_nins = reset_password_user.nins.verified.to_list()
        if verified_nins:
            current_app.logger.info('Unverifying nins for user {state.eppn}')
            reset_password_user.nins.primary.is_primary = False
            for nin in verified_nins:
                nin.is_verified = False
                current_app.logger.debug('NIN {nin.number} unverified')

    reset_password_user = reset_password(reset_password_user, new_password=password,
                                         is_generated=state.generated_password,
                                         application='security', vccs_url=vccs_url)
    reset_password_user.terminated = False
    save_and_sync_user(reset_password_user)
    current_app.stats.count(name='security_password_reset', value=1)
    current_app.logger.info('Reset password successful for user {reset_password_user.eppn}')


def get_extra_security_alternatives(eppn: str) -> dict:
    """
    :param eppn: Users unique eppn
    :return: Dict of alternatives
    """
    alternatives = {}
    user = current_app.central_userdb.get_user_by_eppn(eppn, raise_on_missing=True)

    if user.phone_numbers.verified.count:
        verified_phone_numbers = [item.number for item in user.phone_numbers.verified.to_list()]
        alternatives['phone_numbers'] = verified_phone_numbers
    return alternatives


def mask_alternatives(alternatives: dict) -> dict:
    """
    :param alternatives: Extra security alternatives collected from user
    :return: Masked extra security alternatives
    """
    if alternatives:
        # Phone numbers
        masked_phone_numbers = []
        for phone_number in alternatives.get('phone_numbers', []):
            masked_number = '{}{}'.format('X'*(len(phone_number)-2), phone_number[len(phone_number)-2:])
            masked_phone_numbers.append(masked_number)

        alternatives['phone_numbers'] = masked_phone_numbers
    return alternatives


def verify_email_address(state: ResetPasswordEmailState) -> bool:
    """
    :param state: Password reset state
    """
    user = current_app.central_userdb.get_user_by_eppn(state.eppn,
                                                       raise_on_missing=False)
    if not user:
        current_app.logger.error(f'Could not find user {state.eppn}')
        return False

    proofing_element = MailAddressProofing(user, created_by='security',
                                           mail_address=state.email_address,
                                           reference=state.reference,
                                           proofing_version='2013v1')

    if current_app.proofing_log.save(proofing_element):
        state.email_code.is_verified = True
        current_app.password_reset_state_db.save(state)
        current_app.logger.info(f'Email code marked as used for {state.eppn}')
        return True

    return False


def send_verify_phone_code(state: ResetPasswordEmailState, phone_number: str):
    state = ResetPasswordEmailAndPhoneState.from_email_state(state,
                                            phone_number=phone_number,
                                            phone_code=get_short_hash())
    current_app.password_reset_state_db.save(state)
    template = 'reset_password_sms.txt.jinja2'
    context = {
        'verification_code': state.phone_code.code
    }
    send_sms(state.phone_number, template, context, state.reference)
    current_app.logger.info(f'Sent password reset sms to user {state.eppn}')
    current_app.logger.debug(f'Phone number: {state.phone_number}')


def send_sms(phone_number: str, text_template: str,
             context: Optional[dict] = None,
             reference: Optional[str] = None):
    """
    :param phone_number: the recipient of the sms
    :param text_template: message as a jinja template
    :param context: template context
    :param reference: Audit reference to help cross reference audit log and events
    """
    default_context = {
        "site_url": current_app.config.eduid_site_url,
        "site_name": current_app.config.eduid_site_name,
    }
    if context is None:
        context = {}
    context.update(default_context)

    message = render_template(text_template, **context)
    current_app.msg_relay.sendsms(phone_number, message, reference)


def verify_phone_number(state: ResetPasswordEmailAndPhoneState) -> bool:
    """
    :param state: Password reset state
    """

    user = current_app.central_userdb.get_user_by_eppn(state.eppn,
                                                       raise_on_missing=False)
    if not user:
        current_app.logger.error(f'Could not find user {state.eppn}')
        return False

    proofing_element = PhoneNumberProofing(user, created_by='security',
                                           phone_number=state.phone_number,
                                           reference=state.reference,
                                           proofing_version='2013v1')
    if current_app.proofing_log.save(proofing_element):
        state.phone_code.is_verified = True
        current_app.password_reset_state_db.save(state)
        current_app.logger.info('Phone code marked as used for {state.eppn}')
        return True

    return False
