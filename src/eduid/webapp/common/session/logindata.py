from __future__ import annotations

import logging
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Sequence, TypeVar
from urllib.parse import urlencode

from pydantic import BaseModel

from eduid.webapp.common.session.namespaces import (
    IdP_OtherDevicePendingRequest,
    IdP_PendingRequest,
    IdP_SAMLPendingRequest,
    RequestRef,
)
from eduid.webapp.idp.assurance_data import EduidAuthnContextClass
from eduid.webapp.idp.idp_saml import IdP_SAMLRequest

#
# Copyright (c) 2013, 2014, 2016 NORDUnet A/S. All rights reserved.
# Copyright 2012 Roland Hedberg. All rights reserved.
#
# See the file eduid-IdP/LICENSE.txt for license statement.
#
# Author : Fredrik Thulin <fredrik@thulin.net>
#          Roland Hedberg
#
from eduid.webapp.idp.other_device.data import OtherDeviceId
from eduid.webapp.idp.other_device.db import OtherDevice

logger = logging.getLogger(__name__)


class ExternalMfaData(BaseModel):
    """
    Data about a successful external authentication as a multi factor.
    """

    issuer: str
    authn_context: str
    timestamp: datetime


@dataclass
class LoginContext(ABC):
    """
    Class to hold data about an ongoing login process in memory only.

    Instances of this class is used more or less like a context being passed around.
    None of this data is persisted anywhere.

    This is more or less an interface to the current 'pending_request' in the session,
    identified by the request_ref.
    """

    request_ref: RequestRef
    _pending_request: Optional[IdP_PendingRequest] = field(default=None, init=False, repr=False)

    def __str__(self) -> str:
        return f'<{self.__class__.__name__}: key={self.request_ref}>'

    @property
    def pending_request(self) -> IdP_PendingRequest:
        if self._pending_request is None:
            from eduid.webapp.common.session import session

            pending_request = session.idp.pending_requests.get(self.request_ref)
            if not pending_request:
                raise RuntimeError(f'No pending request with ref {self.request_ref} found in session')
            self._pending_request = pending_request

        return self._pending_request

    @property
    def request_id(self) -> Optional[str]:
        raise NotImplementedError('Subclass must implement request_id')

    @property
    def authn_contexts(self) -> List[str]:
        raise NotImplementedError('Subclass must implement authn_contexts')

    @property
    def reauthn_required(self) -> bool:
        raise NotImplementedError('Subclass must implement reauthn_required')

    @property
    def other_device_state_id(self) -> Optional[OtherDeviceId]:
        """ Get the state_id for the OtherDevice state, if the user wants to log in using another device. """
        raise NotImplementedError('Subclass must implement other_device_state_id')

    @property
    def is_other_device_1(self) -> bool:
        """ Check if this is a request to log in on another device (specifically device #1). """
        raise NotImplementedError('Subclass must implement is_other_device_1')

    @property
    def is_other_device_2(self) -> bool:
        """ Check if this is a request to log in on another device (specifically device #2). """
        raise NotImplementedError('Subclass must implement is_other_device_2')

    def set_other_device_state(self, state_id: Optional[OtherDeviceId]) -> None:
        if isinstance(self.pending_request, IdP_SAMLPendingRequest):
            self.pending_request.other_device_state_id = state_id
        elif isinstance(self.pending_request, IdP_OtherDevicePendingRequest):
            self.pending_request.state_id = None
        else:
            raise TypeError(f'Can\'t set other_device on pending request of type {type(self.pending_request)}')

    def get_requested_authn_context(self) -> Optional[EduidAuthnContextClass]:
        raise NotImplementedError('Subclass must implement get_requested_authn_context')


TLoginContextSubclass = TypeVar('TLoginContextSubclass', bound='LoginContext')


@dataclass
class LoginContextSAML(LoginContext):

    _saml_req: Optional['IdP_SAMLRequest'] = field(default=None, init=False, repr=False)

    @property
    def SAMLRequest(self) -> str:
        pending = self.pending_request
        if not isinstance(pending, IdP_SAMLPendingRequest):
            raise ValueError('Pending request not initialised (or not a SAML request)')
        if not isinstance(pending.request, str):
            raise ValueError('pending_request.request not initialised')
        return pending.request

    @property
    def RelayState(self) -> str:
        pending = self.pending_request
        if not isinstance(pending, IdP_SAMLPendingRequest):
            raise ValueError('Pending request not initialised (or not a SAML request)')
        return pending.relay_state or ''

    @property
    def binding(self) -> str:
        pending = self.pending_request
        if not isinstance(pending, IdP_SAMLPendingRequest):
            raise ValueError('Pending request not initialised (or not a SAML request)')
        if not isinstance(pending.binding, str):
            raise ValueError('pending_request.binding not initialised')
        return pending.binding

    @property
    def query_string(self) -> str:
        qs = {'SAMLRequest': self.SAMLRequest, 'RelayState': self.RelayState}
        return urlencode(qs)

    @property
    def saml_req(self) -> IdP_SAMLRequest:
        if self._saml_req is None:
            # avoid circular import
            from eduid.webapp.idp.app import current_idp_app as current_app

            self._saml_req = IdP_SAMLRequest(
                self.SAMLRequest, self.binding, current_app.IDP, debug=current_app.conf.debug
            )
        return self._saml_req

    @property
    def request_id(self) -> Optional[str]:
        return self.saml_req.request_id

    @property
    def authn_contexts(self) -> List[str]:
        return self.saml_req.get_requested_authn_contexts()

    @property
    def reauthn_required(self) -> bool:
        return self.saml_req.force_authn

    @property
    def other_device_state_id(self) -> Optional[OtherDeviceId]:
        # On device #1, the pending_request has a pointer to the other-device-state
        # Use temporary variable to avoid pycharm warning
        #   Unresolved attribute reference 'other_device_state_id' for class 'IdP_PendingRequest'
        _pending = self.pending_request
        if isinstance(_pending, IdP_SAMLPendingRequest):
            return _pending.other_device_state_id
        return None


    @property
    def is_other_device_1(self) -> bool:
        """ Check if this is a request to log in on another device (specifically device #1).

        If so, since this is an instance of IdP_SAMLPendingRequest (checked in self.other_device_state_id)
        this is a request being processed on the FIRST device. This is the INITIATING device, where the user
        arrived at the Login app with a SAML authentication request, and chose to log in using another device.
        """
        return self.other_device_state_id is not None

    @property
    def is_other_device_2(self) -> bool:
        """ Check if this is a request to log in on another device (specifically device #2).

        return False

    def get_requested_authn_context(self) -> Optional[EduidAuthnContextClass]:
        """
        Check if the SP has explicit Authn preferences in the metadata (some SPs are not
        capable of conveying this preference in the RequestedAuthnContext)

        TODO: Don't just return the first one, but the most relevant somehow.
        """
        res = _pick_authn_context(self.authn_contexts, self.request_ref)

        attributes = self.saml_req.sp_entity_attributes
        if 'http://www.swamid.se/assurance-requirement' in attributes:
            # TODO: This is probably obsolete and not present anywhere in SWAMID metadata anymore
            new_authn = _pick_authn_context(attributes['http://www.swamid.se/assurance-requirement'], self.request_ref)
            logger.debug(
                f'Entity {self.saml_req.sp_entity_id} has AuthnCtx preferences in metadata. '
                f'Overriding {res} -> {new_authn}'
            )
            try:
                res = EduidAuthnContextClass(new_authn)
            except ValueError:
                logger.debug(f'Ignoring unknown authnContextClassRef found in metadata: {new_authn}')
        return res


@dataclass
class LoginContextOtherDevice(LoginContext):

    other_device_req: OtherDevice = field(repr=False)

    @property
    def request_id(self) -> Optional[str]:
        return self.other_device_req.device1.request_id

    @property
    def authn_contexts(self) -> List[str]:
        if not self.other_device_req.device1.authn_context:
            return []
        return [str(self.other_device_req.device1.authn_context)]

    @property
    def reauthn_required(self) -> bool:
        return self.other_device_req.device1.reauthn_required

    @property
    def other_device_state_id(self) -> Optional[OtherDeviceId]:
        # On device #2, the pending request is the other-device-state
        _pending = self.pending_request
        if isinstance(_pending, IdP_OtherDevicePendingRequest):
            return _pending.state_id
        return None

    @property
    def is_other_device_1(self) -> bool:
        """ Check if this is a request to log in on another device (specifically device #1). """
        return False

    @property
    def is_other_device_2(self) -> bool:
        """ Check if this is a request to log in on another device (specifically device #2).

        If so, since this is an instance of IdP_OtherDevicePendingRequest (checked in self.other_device_state_id)
        this is a request being processed on the SECOND device. This is the AUTHENTICATING device, where the user
        has used a camera to scan the QR code shown on the OTHER device (first, initiating)."""
        return self.other_device_state_id is not None

    def get_requested_authn_context(self) -> Optional[EduidAuthnContextClass]:
        """
        Return the authn context (if any) that was originally requested on the first device.

        TODO: Don't just return the first one, but the most relevant somehow.
        """
        return _pick_authn_context(self.authn_contexts, self.request_ref)


def _pick_authn_context(accrs: Sequence[str], log_tag: str) -> Optional[EduidAuthnContextClass]:
    if len(accrs) > 1:
        logger.warning(f'{log_tag}: More than one authnContextClassRef, using the first recognised: {accrs}')
    # first, select the ones recognised by this IdP
    known = []
    for x in accrs:
        try:
            known += [EduidAuthnContextClass(x)]
        except ValueError:
            logger.debug(f'Ignoring unknown authnContextClassRef: {x}')
    if not known:
        return None
    # TODO: Pick the most applicable somehow, not just the first one in the list
    return known[0]
