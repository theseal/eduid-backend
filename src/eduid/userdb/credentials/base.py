# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 SUNET
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
# Author : Fredrik Thulin <fredrik@thulin.net>
#

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from eduid.userdb.element import VerifiedElement

__author__ = "ft"


# well-known proofing methods
class CredentialProofingMethod(str, Enum):
    SWAMID_AL2_MFA = "SWAMID_AL2_MFA"
    SWAMID_AL2_MFA_HI = "SWAMID_AL2_MFA_HI"


class Credential(VerifiedElement):
    """
    Base class for credentials.

    Adds 'proofing_method' to VerifiedElement. Maybe that could benefit the
    main VerifiedElement, but after a short discussion we chose to add it
    only for credentials until we know we want it for other types of verified
    elements too.

    There is some use of these objects as keys in dicts in eduid-IdP,
    so we are making them hashable.
    """

    proofing_method: Optional[CredentialProofingMethod] = None
    proofing_version: Optional[str] = None

    def __str__(self):
        if len(self.key) == 24:
            # probably an object id in string format, don't cut it
            shortkey = str(self.key)
        else:
            shortkey = str(self.key[:12]) + "..."
        if self.is_verified:
            return (
                f"<eduID {self.__class__.__name__}(key={repr(shortkey)}): verified=True, "
                f"proofing=({repr(self.proofing_method)} v={repr(self.proofing_version)})>"
            )
        else:
            return f"<eduID {self.__class__.__name__}(key={repr(shortkey)}): verified=False>"

    def _to_dict_transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make sure we never store proofing info for un-verified credentials
        """
        data = super()._to_dict_transform(data)

        if data.get("verified") is False:
            del data["verified"]
            if "proofing_method" in data:
                del data["proofing_method"]
            if "proofing_version" in data:
                del data["proofing_version"]
        return data
