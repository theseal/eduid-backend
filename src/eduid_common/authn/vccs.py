#
# Copyright (c) 2015, 2016 NORDUnet A/S
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
import logging
from typing import Optional

from bson import ObjectId
from vccs_client import VCCSClient, VCCSClientHTTPError, VCCSPasswordFactor, VCCSRevokeFactor

from eduid_common.api.decorators import deprecated
from eduid_userdb.credentials import Password
from eduid_userdb.user import User

logger = logging.getLogger(__name__)


def get_vccs_client(vccs_url: Optional[str]) -> VCCSClient:
    """
    Instantiate a VCCS client.

    :param vccs_url: VCCS authentication backend URL
    :return: vccs client
    """
    return VCCSClient(base_url=vccs_url)


def check_password(
    password: str, user: User, vccs_url: Optional[str] = None, vccs: Optional[VCCSClient] = None
) -> Optional[Password]:
    """
    Try to validate a user provided password.

    :param password: plaintext password
    :param user: User object
    :param vccs_url: URL to VCCS authentication backend
    :param vccs: Optional already instantiated vccs client

    :return: Password credential on success
    """
    if vccs is None:
        vccs = get_vccs_client(vccs_url)

    for user_password in user.credentials.filter(Password).to_list():
        factor = VCCSPasswordFactor(password, credential_id=str(user_password.key), salt=user_password.salt)
        try:
            if vccs.authenticate(str(user.user_id), [factor]):
                return user_password
        except Exception:
            logger.exception(f'VCCS authentication for user {user} factor {factor} failed')
    return None


def add_password(
    user: User,
    new_password: str,
    application: str,
    is_generated: bool = False,
    vccs_url: Optional[str] = None,
    vccs: Optional[VCCSClient] = None,
) -> bool:
    """
    :param user: User object
    :param new_password: plaintext new password
    :param application: Application requesting credential change
    :param vccs_url: URL to VCCS authentication backend
    :param vccs: Optional already instantiated vccs client

    :return: Success or not
    """
    if vccs is None:
        vccs = get_vccs_client(vccs_url)

    # TODO: Init VCCSPasswordFactor with password hash instead of plain text password
    new_factor = VCCSPasswordFactor(new_password, credential_id=str(ObjectId()))

    # Add the new password
    if not vccs.add_credentials(str(user.user_id), [new_factor]):
        logger.error('Failed adding password credential {} for user {}'.format(new_factor.credential_id, user))
        return False  # something failed
    logger.info('Added password credential {} for user {}'.format(new_factor.credential_id, user))

    # Add new password to user
    _password = Password(
        credential_id=new_factor.credential_id, salt=new_factor.salt, is_generated=is_generated, created_by=application
    )
    user.credentials.add(_password)
    return True


def reset_password(
    user: User,
    new_password: str,
    application: str,
    is_generated: bool = False,
    vccs_url: Optional[str] = None,
    vccs: Optional[VCCSClient] = None,
) -> bool:
    """
    :param user: User object
    :param new_password: plaintext new password
    :param application: Application requesting credential change
    :param vccs_url: URL to VCCS authentication backend
    :param vccs: Optional already instantiated vccs client

    :return: Success or not
    """
    if vccs is None:
        vccs = get_vccs_client(vccs_url)

    # TODO: Init VCCSPasswordFactor with password hash instead of plain text password
    new_factor = VCCSPasswordFactor(new_password, credential_id=str(ObjectId()))

    # Revoke all existing passwords
    if not revoke_passwords(user, 'password reset', application=application, vccs=vccs):
        # TODO: Not sure if ignoring errors is the right thing to do here. Old credential might be compromised.
        logger.error(f'Failed revoking password credentials for user {user} - proceeding anyways')

    # Add the new password
    if not vccs.add_credentials(str(user.user_id), [new_factor]):
        logger.error('Failed adding password credential {} for user {}'.format(new_factor.credential_id, user))
        return False  # something failed
    logger.info('Added password credential {} for user {}'.format(new_factor.credential_id, user))

    # Add new password to user
    _password = Password(
        credential_id=new_factor.credential_id, salt=new_factor.salt, is_generated=is_generated, created_by=application
    )
    user.credentials.add(_password)
    return True


def change_password(
    user: User,
    new_password: str,
    old_password: str,
    application: str,
    is_generated: bool = False,
    vccs_url: Optional[str] = None,
    vccs: Optional[VCCSClient] = None,
) -> bool:
    """
    :param user: User object
    :param new_password: Plaintext new password
    :param old_password: Plaintext current password
    :param application: Application requesting credential change
    :param vccs_url: URL to VCCS authentication backend
    :param vccs: Optional already instantiated vccs client

    :return: Success or not
    """
    if vccs is None:
        vccs = get_vccs_client(vccs_url)

    # TODO: Init VCCSPasswordFactor with password hash instead of plain text password
    new_factor = VCCSPasswordFactor(new_password, credential_id=str(ObjectId()))
    del new_password  # don't need it anymore, try to forget it

    # Check the old password and turn it in to a RevokeFactor
    checked_password = check_password(old_password, user, vccs_url=vccs_url, vccs=vccs)
    del old_password  # don't need it anymore, try to forget it
    if not checked_password:
        logger.error('Old password did not match for user {}'.format(user))
        return False
    revoke_factor = VCCSRevokeFactor(str(checked_password.credential_id), 'changing password', reference=application)

    # Add the new password
    if not vccs.add_credentials(str(user.user_id), [new_factor]):
        logger.error('Failed adding password credential {} for user {}'.format(new_factor.credential_id, user))
        return False  # something failed
    logger.info('Added password credential {} for user {}'.format(new_factor.credential_id, user))

    # Revoke the old password
    vccs.revoke_credentials(str(user.user_id), [revoke_factor])
    user.credentials.remove(checked_password.credential_id)
    logger.info('Revoked credential {} for user {}'.format(revoke_factor.credential_id, user))

    # Add new password to user
    _password = Password(
        credential_id=new_factor.credential_id, salt=new_factor.salt, is_generated=is_generated, created_by=application
    )
    user.credentials.add(_password)
    return True


@deprecated
def add_credentials(
    old_password: Optional[str],
    new_password: str,
    user: User,
    source: str,
    vccs_url: Optional[str] = None,
    vccs: Optional[VCCSClient] = None,
) -> bool:
    """
    Add a new password to a user. Revokes the old one, if one is given.
    Revokes all old passwords if no old one is given - password reset.

    :param user: User object
    :param new_password: plaintext new password
    :param source: Application requesting credential change
    :param old_password: Plaintext current password
    :param vccs_url: URL to VCCS authentication backend
    :param vccs: Optional already instantiated vccs client

    :return: Success status
    """
    if vccs is None:
        vccs = get_vccs_client(vccs_url)

    new_factor = VCCSPasswordFactor(new_password, credential_id=str(ObjectId()))

    checked_password = None
    # remember if an old password was supplied or not, without keeping it in
    # memory longer than we have to
    old_password_supplied = bool(old_password)
    if user.credentials.filter(Password).count > 0 and old_password_supplied:
        assert old_password is not None  # mypy doesn't get that old_password can't be None here
        # Find the old credential to revoke
        checked_password = check_password(old_password, user, vccs_url=vccs_url, vccs=vccs)
        del old_password  # don't need it anymore, try to forget it
        if not checked_password:
            return False

    if not vccs.add_credentials(str(user.user_id), [new_factor]):
        logger.warning("Failed adding password credential {!r} for user {!r}".format(new_factor.credential_id, user))
        return False  # something failed
    logger.debug("Added password credential {!s} for user {!s}".format(new_factor.credential_id, user))

    if checked_password:
        old_factor = VCCSRevokeFactor(str(checked_password.credential_id), 'changing password', reference=source)
        vccs.revoke_credentials(str(user.user_id), [old_factor])
        user.credentials.remove(checked_password.credential_id)
        logger.debug("Revoked old credential {!s} (user {!s})".format(old_factor.credential_id, user))

    if not old_password_supplied:
        # XXX: Revoke all current credentials on password reset for now
        revoked = []
        for password in user.credentials.filter(Password).to_list():
            revoked.append(VCCSRevokeFactor(str(password.credential_id), 'reset password', reference=source))
            logger.debug(
                "Revoking old credential (password reset) " "{!s} (user {!s})".format(password.credential_id, user)
            )
            user.credentials.remove(password.credential_id)
        if revoked:
            try:
                vccs.revoke_credentials(str(user.user_id), revoked)
            except VCCSClientHTTPError:
                # Password already revoked
                # TODO: vccs backend should be changed to return something more informative than
                # TODO: VCCSClientHTTPError when the credential is already revoked or just return success.
                logger.warning("VCCS failed to revoke all passwords for " "user {!s}".format(user))

    _new_cred = Password(credential_id=new_factor.credential_id, salt=new_factor.salt, created_by=source)
    user.credentials.add(_new_cred)
    return True


def revoke_passwords(
    user: User, reason: str, application: str, vccs_url: Optional[str] = None, vccs: Optional[VCCSClient] = None
) -> bool:
    """
    :param user: User object
    :param reason: Reason for revoking all passwords
    :param application: Application requesting credential change
    :param vccs_url: URL to VCCS authentication backend
    :param vccs: Optional already instantiated vccs client

    :return: Success or not
    """
    if vccs is None:
        vccs = get_vccs_client(vccs_url)

    revoke_factors = []
    for password in user.credentials.filter(Password).to_list():
        credential_id = str(password.key)
        factor = VCCSRevokeFactor(credential_id, reason, reference=application)
        logger.debug(f'Revoking credential {credential_id} for user {user} with reason "{reason}"')
        revoke_factors.append(factor)
        user.credentials.remove(password.key)

    userid = str(user.user_id)
    try:
        vccs.revoke_credentials(userid, revoke_factors)
    except VCCSClientHTTPError:
        # One of the passwords was already revoked
        # TODO: vccs backend should be changed to return something more informative than
        # TODO: VCCSClientHTTPError when the credential is already revoked or just return success.
        logger.warning(f'VCCS failed to revoke all passwords for user {user}')
        return False
    return True


@deprecated
def revoke_all_credentials(
    user, source='dashboard', vccs_url: Optional[str] = None, vccs: Optional[VCCSClient] = None
) -> None:
    if vccs is None:
        vccs = get_vccs_client(vccs_url)
    to_revoke = []
    for password in user.credentials.filter(Password).to_list():
        credential_id = str(password.credential_id)
        factor = VCCSRevokeFactor(credential_id, 'subscriber requested termination', reference=source)
        logger.debug("Revoked old credential (account termination) {!s} (user {!s})".format(credential_id, user))
        to_revoke.append(factor)
    userid = str(user.user_id)
    vccs.revoke_credentials(userid, to_revoke)
