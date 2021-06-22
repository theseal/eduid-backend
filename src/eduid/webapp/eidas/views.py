# -*- coding: utf-8 -*-
from typing import Union
from uuid import uuid4

from dateutil.parser import parse as dt_parse
from flask import Blueprint, abort, make_response, redirect, request, url_for
from werkzeug.wrappers import Response as WerkzeugResponse

from eduid.common.config.base import EduidEnvironment
from eduid.userdb import User
from eduid.userdb.credentials.base import CredentialKey
from eduid.userdb.credentials.fido import FidoCredential
from eduid.webapp.common.api.decorators import MarshalWith, require_user
from eduid.webapp.common.api.helpers import check_magic_cookie
from eduid.webapp.common.api.messages import FluxData, redirect_with_msg, success_response
from eduid.webapp.common.api.schemas.csrf import EmptyResponse
from eduid.webapp.common.api.utils import urlappend
from eduid.webapp.common.authn.acs_enums import EidasAcsAction
from eduid.webapp.common.authn.acs_registry import get_action, schedule_action
from eduid.webapp.common.authn.eduid_saml2 import BadSAMLResponse, get_authn_response
from eduid.webapp.common.authn.utils import get_location
from eduid.webapp.common.session import session
from eduid.webapp.common.session.namespaces import AuthnRequestRef, SP_AuthnRequest
from eduid.webapp.eidas.acs_actions import nin_verify_BACKDOOR
from eduid.webapp.eidas.app import current_eidas_app as current_app
from eduid.webapp.eidas.helpers import EidasMsg, create_authn_request, create_metadata, staging_nin_remap

__author__ = 'lundberg'

eidas_views = Blueprint('eidas', __name__, url_prefix='', template_folder='templates')


@eidas_views.route('/', methods=['GET'])
@MarshalWith(EmptyResponse)
@require_user
def index(user) -> FluxData:
    return success_response(payload=None, message=None)


@eidas_views.route('/verify-token/<credential_id>', methods=['GET'])
@require_user
def verify_token(user: User, credential_id: CredentialKey) -> Union[FluxData, WerkzeugResponse]:
    current_app.logger.debug('verify-token called with credential_id: {}'.format(credential_id))
    redirect_url = current_app.conf.token_verify_redirect_url

    # Check if requested key id is a mfa token and if the user used that to log in
    token_to_verify = user.credentials.filter(FidoCredential).find(credential_id)
    if not token_to_verify:
        return redirect_with_msg(redirect_url, EidasMsg.token_not_found)
    if token_to_verify.key not in session.get('eduidIdPCredentialsUsed', []):
        # If token was not used for login, reauthn the user
        current_app.logger.info('Token {} not used for login, redirecting to authn'.format(token_to_verify.key))
        ts_url = current_app.conf.token_service_url
        reauthn_url = urlappend(ts_url, 'reauthn')
        next_url = url_for('eidas.verify_token', credential_id=credential_id, _external=True)
        # Add idp arg to next_url if set
        idp = request.args.get('idp')
        if idp:
            next_url = f'{next_url}?idp={idp}'
        redirect_url = f'{reauthn_url}?next={next_url}'
        current_app.logger.debug(f'Redirecting user to {redirect_url}')
        return redirect(redirect_url)

    # Set token key id in session
    session.eidas.verify_token_action_credential_id = credential_id

    # Request a authentication from idp
    required_loa = 'loa3'
    return _authn(EidasAcsAction.token_verify, required_loa, force_authn=True)


@eidas_views.route('/verify-nin', methods=['GET'])
@require_user
def verify_nin(user: User) -> WerkzeugResponse:
    current_app.logger.debug('verify-nin called')

    # Backdoor for the selenium integration tests to verify NINs
    # without sending the user to an eidas idp
    if check_magic_cookie(current_app.conf):
        return nin_verify_BACKDOOR()

    required_loa = 'loa3'
    return _authn(EidasAcsAction.nin_verify, required_loa, force_authn=True)


@eidas_views.route('/mfa-authentication', methods=['GET'])
def mfa_authentication() -> WerkzeugResponse:
    current_app.logger.debug('mfa-authentication called')
    required_loa = 'loa3'
    # Clear session keys used for external mfa
    del session.mfa_action
    return _authn(EidasAcsAction.mfa_authn, required_loa, force_authn=True)


def _authn(
    action: EidasAcsAction, required_loa: str, force_authn: bool = False, redirect_url: str = '/'
) -> WerkzeugResponse:
    """
    :param action: name of action
    :param required_loa: friendly loa name
    :param force_authn: should a new authentication be forced
    :param redirect_url: redirect url after successful authentication

    :return: redirect response
    """
    redirect_url = request.args.get('next', redirect_url)
    _authn_id = AuthnRequestRef(str(uuid4()))
    session.eidas.sp.authns[_authn_id] = SP_AuthnRequest(post_authn_action=action, redirect_url=redirect_url)
    current_app.logger.debug(f'Stored SP_AuthnRequest[{_authn_id}]: {session.eidas.sp.authns[_authn_id]}')

    idp = request.args.get('idp')
    current_app.logger.debug(f'Requested IdP: {idp}')
    idps = current_app.saml2_config.metadata.identity_providers()
    current_app.logger.debug(f'IdPs from metadata: {idps}')

    if idp is not None and idp in idps:
        authn_request = create_authn_request(
            relay_state=_authn_id, selected_idp=idp, required_loa=required_loa, force_authn=force_authn,
        )
        # TODO: Remove, replaced by session.eidas.sp.authns above
        schedule_action(action, session.eidas.sp)
        current_app.logger.info(f'Redirecting the user to {idp} for {action}')
        return redirect(get_location(authn_request))
    abort(make_response('Requested IdP not found in metadata', 404))


@eidas_views.route('/saml2-acs', methods=['POST'])
def assertion_consumer_service() -> WerkzeugResponse:
    """
    Assertion consumer service, receives POSTs from SAML2 IdP's
    """

    if 'SAMLResponse' not in request.form:
        abort(400)

    saml_response = request.form['SAMLResponse']
    try:
        authn_response, _authn_id = get_authn_response(
            current_app.saml2_config, session.eidas.sp, session, saml_response
        )
    except BadSAMLResponse as e:
        current_app.logger.error(f'BadSAMLResponse: {e}')
        return make_response(str(e), 400)

    unsolicited_response_redirect_url = current_app.conf.unsolicited_response_redirect_url
    if _authn_id not in session.eidas.sp.authns:
        current_app.logger.info(f'Unknown response. Redirecting user to {unsolicited_response_redirect_url}')
        return redirect(unsolicited_response_redirect_url)

    session_info = authn_response.session_info()

    current_app.logger.debug(f'Auth response:\n{authn_response}\n\n')
    current_app.logger.debug(f'Session info:\n{session_info}\n\n')

    # Remap nin in staging environment
    if current_app.conf.environment == EduidEnvironment.staging:
        session_info = staging_nin_remap(session_info)

    authn_data = session.eidas.sp.authns.get(_authn_id)
    authn_data.authn_instant = dt_parse(session_info['authn_info'][0][2])

    action = get_action(default_action=None, sp_data=session.eidas.sp, authndata=authn_data)
    return action(session_info, authndata=authn_data)


@eidas_views.route('/saml2-metadata')
def metadata() -> WerkzeugResponse:
    """
    Returns an XML with the SAML 2.0 metadata for this
    SP as configured in the saml2_settings.py file.
    """
    data = create_metadata(current_app.saml2_config)
    response = make_response(data.to_string(), 200)
    response.headers['Content-Type'] = "text/xml; charset=utf8"
    return response
