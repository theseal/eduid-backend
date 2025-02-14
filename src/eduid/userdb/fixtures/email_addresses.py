# -*- coding: utf-8 -*-
#
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
#     3. Neither the name of the SUNET nor the names of its
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
from datetime import datetime

from eduid.userdb.mail import MailAddress

johnsmith_example_com = MailAddress.from_dict(
    {
        "email": "johnsmith@example.com",
        "created_by": "signup",
        "created_ts": datetime.fromisoformat("2013-09-02T10:23:25"),
        "verified": True,
        "verified_by": "signup",
        "verified_ts": datetime.fromisoformat("2013-09-02T10:23:25"),
        "primary": True,
    }
)


johnsmith2_example_com = MailAddress.from_dict(
    {
        "email": "johnsmith2@example.com",
        "created_by": "dashboard",
        "created_ts": datetime.fromisoformat("2013-09-02T10:23:25"),
        "verified": False,
        "verified_by": "dashboard",
        "verified_ts": datetime.fromisoformat("2013-09-02T10:23:25"),
        "primary": False,
    }
)


johnsmith3_example_com = MailAddress.from_dict(
    {
        "email": "johnsmith3@example.com",
        "created_by": "signup",
        "created_ts": datetime.fromisoformat("2017-01-04T15:47:27"),
        "verified": True,
        "verified_by": "signup",
        "verified_ts": datetime.fromisoformat("2017-01-04T16:47:27"),
        "primary": True,
    }
)


johnsmith_example_com_old = MailAddress.from_dict({"email": "johnsmith@example.com", "verified": True, "primary": True})


johnsmith2_example_com_old = MailAddress.from_dict({"email": "johnsmith2@example.com", "verified": True})


johnsmith3_example_com_unverified = MailAddress.from_dict({"email": "johnsmith3@example.com", "verified": False})


johnsmith_example_org = MailAddress.from_dict(
    {
        "email": "johnsmith@example.org",
        "created_by": "signup",
        "created_ts": datetime.fromisoformat("2013-09-02T10:23:25"),
        "verified": True,
        "verified_by": "signup",
        "verified_ts": datetime.fromisoformat("2013-09-02T10:23:25"),
        "primary": True,
    }
)


johnsmith2_example_org = MailAddress.from_dict(
    {
        "email": "johnsmith2@example.org",
        "created_by": "dashboard",
        "created_ts": datetime.fromisoformat("2013-09-02T10:23:25"),
        "verified": False,
        "verified_by": "dashboard",
        "verified_ts": datetime.fromisoformat("2013-09-02T10:23:25"),
        "primary": False,
    }
)
