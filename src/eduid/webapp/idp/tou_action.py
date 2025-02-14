#
# Copyright (c) 2015 NORDUnet A/S
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

__author__ = "eperez"

import logging
from typing import Optional

from eduid.userdb.idp import IdPUser
from eduid.webapp.idp.app import current_idp_app as current_app
from eduid.webapp.idp.login_context import LoginContext

logger = logging.getLogger(__name__)


def need_tou_acceptance(user: IdPUser) -> bool:
    """
    Check if the user is required to accept a new version of the Terms of Use,
    in case the IdP configuration points to a version the user hasn't accepted,
    or the old acceptance was too long ago.
    """
    version = current_app.conf.tou_version
    interval = current_app.conf.tou_reaccept_interval

    if user.tou.has_accepted(version, int(interval.total_seconds())):
        logger.debug(f"User has already accepted ToU version {repr(version)}")
        return False

    tous = [x.version for x in user.tou.to_list()]
    logger.info(f"User needs to accepted ToU version {repr(version)} (has accepted: {tous})")

    return True
