# -*- coding: utf-8 -*-


from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from iso3166 import countries

from eduid.common.config.base import ProofingConfigMixin
from eduid.common.rpc.exceptions import AmTaskFailed, MsgTaskFailed, NoNavetData
from eduid.userdb import User
from eduid.userdb.credentials import Credential
from eduid.userdb.element import ElementKey
from eduid.userdb.identity import IdentityElement, IdentityType, SvipeIdentity
from eduid.userdb.logs.element import NinProofingLogElement, SvipeIDForeignProofing, SvipeIDNINProofing
from eduid.userdb.proofing import NinProofingElement, ProofingUser
from eduid.userdb.proofing.state import NinProofingState
from eduid.webapp.common.api.helpers import set_user_names_from_foreign_id, verify_nin_for_user
from eduid.webapp.common.api.messages import CommonMsg
from eduid.webapp.common.proofing.base import (
    MatchResult,
    ProofingElementResult,
    ProofingFunctions,
    VerifyCredentialResult,
    VerifyUserResult,
)
from eduid.webapp.common.proofing.methods import ProofingMethod
from eduid.webapp.svipe_id.app import current_svipe_id_app as current_app
from eduid.webapp.svipe_id.helpers import SvipeDocumentUserInfo

__author__ = "lundberg"


@dataclass
class SvipeIDProofingFunctions(ProofingFunctions[SvipeDocumentUserInfo]):
    def is_swedish_document(self) -> bool:
        issuing_country = countries.get(self.session_info.document_issuing_country, None)
        sweden = countries.get("SE")
        if not sweden:
            raise RuntimeError('Could not find country "SE" in iso3166')
        if not issuing_country:
            raise RuntimeError(f'Could not find country "{self.session_info.document_issuing_country}" in iso3166')
        if issuing_country == sweden:
            return True
        return False

    def get_identity(self, user: User) -> Optional[IdentityElement]:
        if self.is_swedish_document():
            return user.identities.nin
        return user.identities.svipe

    def verify_identity(self, user: User) -> VerifyUserResult:
        if self.is_swedish_document():
            return self._verify_nin_identity(user)
        return self._verify_foreign_identity(user)

    def _verify_nin_identity(self, user: User) -> VerifyUserResult:
        proofing_user = ProofingUser.from_user(user, current_app.private_userdb)

        # Create a proofing log
        proofing_log_entry = self.identity_proofing_element(user=user)
        if proofing_log_entry.error:
            return VerifyUserResult(error=proofing_log_entry.error)
        assert isinstance(proofing_log_entry.data, NinProofingLogElement)  # please type checking

        # Verify NIN for user
        try:
            nin_element = NinProofingElement(
                number=self.session_info.document_administrative_number,
                created_by=current_app.conf.app_name,
                is_verified=False,
            )
            proofing_state = NinProofingState(id=None, modified_ts=None, eppn=proofing_user.eppn, nin=nin_element)
            if not verify_nin_for_user(proofing_user, proofing_state, proofing_log_entry.data):
                current_app.logger.error(f"Failed verifying NIN for user {proofing_user}")
                return VerifyUserResult(error=CommonMsg.temp_problem)
        except AmTaskFailed:
            current_app.logger.exception("Verifying NIN for user failed")
            return VerifyUserResult(error=CommonMsg.temp_problem)

        current_app.stats.count(name="nin_verified")
        # re-load the user from central db before returning
        _user = current_app.central_userdb.get_user_by_eppn(proofing_user.eppn)
        assert _user is not None  # please mypy
        return VerifyUserResult(user=ProofingUser.from_user(_user, current_app.private_userdb))

    def _verify_foreign_identity(self, user: User) -> VerifyUserResult:
        proofing_user = ProofingUser.from_user(user, current_app.private_userdb)

        existing_identity = user.identities.svipe
        locked_identity = user.locked_identity.svipe

        date_of_birth = self.session_info.birthdate
        new_identity = SvipeIdentity(
            created_by=current_app.conf.app_name,
            date_of_birth=datetime(year=date_of_birth.year, month=date_of_birth.month, day=date_of_birth.day),
            country_code=self.session_info.document_nationality,
            verified_by=current_app.conf.app_name,
            is_verified=True,
            svipe_id=self.session_info.svipe_id,
        )

        # check if the just verified identity matches the locked identity
        if locked_identity is not None and locked_identity.svipe_id != new_identity.svipe_id:
            if not self._can_replace_identity(proofing_user=proofing_user):
                # asserted identity did not match the locked identity
                return VerifyUserResult(error=CommonMsg.locked_identity_not_matching)
            # replace the locked identity as the users asserted prid has changed,
            # and we are sure enough that it is the same person
            proofing_user.locked_identity.replace(element=new_identity)

        # the existing identity is not verified, just remove it
        if existing_identity is not None:
            proofing_user.identities.remove(key=ElementKey(IdentityType.SVIPE))

        # everything seems to check out, add the new identity to the user
        proofing_user.identities.add(element=new_identity)

        # Create a proofing log
        proofing_log_entry = self.identity_proofing_element(user=proofing_user)
        if proofing_log_entry.error:
            return VerifyUserResult(error=proofing_log_entry.error)
        assert isinstance(proofing_log_entry.data, SvipeIDForeignProofing)  # please type checking

        # update the users names from the verified identity
        proofing_user = set_user_names_from_foreign_id(proofing_user, proofing_log_entry.data)

        # Verify Svipe identity for user
        if not current_app.proofing_log.save(proofing_log_entry.data):
            current_app.logger.error("Failed to save Svipe identity proofing log for user")
            return VerifyUserResult(error=CommonMsg.temp_problem)
        try:
            # Save user to private db
            current_app.private_userdb.save(proofing_user)
            # Ask am to sync user to central db
            current_app.logger.info(f"Request sync for user")
            result = current_app.am_relay.request_user_sync(proofing_user)
            current_app.logger.info(f"Sync result for user: {result}")
        except AmTaskFailed:
            current_app.logger.exception("Verifying Svipe identity for user failed")
            return VerifyUserResult(error=CommonMsg.temp_problem)

        current_app.stats.count(name="foreign_identity_verified")
        # load the user from central db before returning
        _user = current_app.central_userdb.get_user_by_eppn(proofing_user.eppn)
        assert _user is not None  # please mypy
        return VerifyUserResult(user=_user)

    def _can_replace_identity(self, proofing_user: ProofingUser) -> bool:
        locked_identity = proofing_user.locked_identity.svipe
        if locked_identity is None:
            return True
        # svipe id should stay the same, but it is not impossible that it has changed
        # try to verify that it is the same person with a new svipe id
        date_of_birth_matches = locked_identity.date_of_birth.date() == self.session_info.birthdate
        given_name_matches = proofing_user.given_name == self.session_info.given_name
        surname_matches = proofing_user.surname == self.session_info.family_name
        if date_of_birth_matches and given_name_matches and surname_matches:
            return True
        return False

    def identity_proofing_element(self, user: User) -> ProofingElementResult:

        if self.backdoor:
            # TODO: implement backdoor support?
            pass

        if self.is_swedish_document():
            return self._nin_identity_proofing_element(user)
        return self._foreign_identity_proofing_element(user)

    def _nin_identity_proofing_element(self, user: User) -> ProofingElementResult:
        _nin = self.session_info.document_administrative_number

        try:
            navet_proofing_data = self._get_navet_data(nin=_nin)
        except NoNavetData:
            current_app.logger.exception("No data returned from Navet")
            return ProofingElementResult(error=CommonMsg.no_navet_data)
        except MsgTaskFailed:
            current_app.logger.exception("Navet lookup failed")
            current_app.stats.count("navet_error")
            return ProofingElementResult(error=CommonMsg.navet_error)

        data = SvipeIDNINProofing(
            created_by=current_app.conf.app_name,
            deregistration_information=navet_proofing_data.deregistration_information,
            eppn=user.eppn,
            nin=_nin,
            svipe_id=self.session_info.svipe_id,
            document_type=self.session_info.document_type_sdn_en,  # standardised name in English (e.g. "Passport")
            document_number=self.session_info.document_number,
            proofing_version=current_app.conf.svipe_id_proofing_version,
            user_postal_address=navet_proofing_data.user_postal_address,
        )
        return ProofingElementResult(data=data)

    def _foreign_identity_proofing_element(self, user: User) -> ProofingElementResult:
        data = SvipeIDForeignProofing(
            created_by=current_app.conf.app_name,
            eppn=user.eppn,
            svipe_id=self.session_info.svipe_id,
            document_type=self.session_info.document_type_sdn_en,  # standardised name in English (e.g. "Passport")
            document_number=self.session_info.document_number,
            proofing_version=current_app.conf.svipe_id_proofing_version,
            given_name=self.session_info.given_name,
            surname=self.session_info.family_name,
            date_of_birth=self.session_info.birthdate.isoformat(),
            country_code=self.session_info.document_nationality,
            administrative_number=self.session_info.document_administrative_number,
            issuing_country=self.session_info.document_issuing_country,
        )
        return ProofingElementResult(data=data)

    def match_identity(self, user: User, proofing_method: ProofingMethod) -> MatchResult:
        raise NotImplementedError("No support for mfa")

    def credential_proofing_element(self, user: User, credential: Credential) -> ProofingElementResult:
        raise NotImplementedError("No support for credential proofing")

    def mark_credential_as_verified(self, credential: Credential, loa: Optional[str]) -> VerifyCredentialResult:
        raise NotImplementedError("No support for credential proofing")


def get_proofing_functions(
    session_info: SvipeDocumentUserInfo,
    app_name: str,
    config: ProofingConfigMixin,
    backdoor: bool,
) -> ProofingFunctions:
    return SvipeIDProofingFunctions(session_info=session_info, app_name=app_name, config=config, backdoor=backdoor)
