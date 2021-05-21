#
# Copyright (c) 2013, 2014, 2015 NORDUnet A/S
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
# Author : Enrique Perez <enrique@cazalla.net>
#
from typing import Optional

from flask import redirect
from werkzeug.wrappers import Response as WerkzeugResponse

from eduid.userdb.idp import IdPUser
from eduid.webapp.common.session import session
from eduid.webapp.common.session.logindata import SSOLoginData
from eduid.webapp.idp import mfa_action, tou_action
from eduid.webapp.idp.app import current_idp_app as current_app
from eduid.webapp.idp.sso_session import SSOSession


def check_for_pending_actions(
    user: IdPUser, ticket: SSOLoginData, sso_session: SSOSession
) -> Optional[WerkzeugResponse]:
    """
    Check whether there are any pending actions for the current user,
    and if there are, redirect to the actions app.

    :param user: the authenticating user
    :param ticket: SSOLoginData instance
    :param sso_session: SSOSession
    """

    if current_app.actions_db is None:
        current_app.logger.info('This IdP is not initialized for special actions')
        return None

    # Add any actions that may depend on the login data
    add_idp_initiated_actions(user, ticket, sso_session)

    actions_eppn = current_app.actions_db.get_actions(user.eppn, session=ticket.request_ref)

    # Check for pending actions
    pending_actions = [a for a in actions_eppn if a.result is None]
    if not pending_actions:
        current_app.logger.debug(f'There are no pending actions for user {user}')
        return None

    # Pending actions found, redirect to the actions app
    current_app.logger.debug(f'There are pending actions for user {user}: {pending_actions}')

    actions_uri = current_app.conf.actions_app_uri
    current_app.logger.info(f'Redirecting user {user} to actions app {actions_uri}')

    # TODO: The IdP should never _write_ to the actions namespace. Actions should _read_
    #       the ticket.request_ref from the IdP namespace instead.
    session.actions.session = ticket.request_ref
    return redirect(actions_uri)


def add_idp_initiated_actions(user: IdPUser, ticket: SSOLoginData, sso_session: SSOSession) -> None:
    """
    Load the configured action plugins and execute their `add_actions`
    functions.
    These functions take the IdP app, the user, and the login data (ticket)
    and add actions that depend on those.

    Also iterate over add_actions entry points and execute them (for backwards
    compatibility).

    :param user: the authenticating user
    :param ticket: the SSO login data
    """
    if 'mfa' in current_app.conf.action_plugins:
        mfa_action.add_actions(user, ticket, sso_session)
    if 'tou' in current_app.conf.action_plugins:
        tou_action.add_actions(user, ticket)
