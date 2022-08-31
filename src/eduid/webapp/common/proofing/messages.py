from enum import unique

from eduid.webapp.common.api.messages import TranslatableMsg


@unique
class ProofingMsg(TranslatableMsg):
    identity_already_verified = 'proofing.identity_already_verified'
    attribute_missing = 'proofing.attribute_missing'
    malformed_identity = 'proofing.malformed_identity'
