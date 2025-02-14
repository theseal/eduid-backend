# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Sunet
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

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping

from eduid.queue.db import Payload

__author__ = "lundberg"


@dataclass
class EduidTestPayload(Payload):
    counter: int

    @classmethod
    def from_dict(cls, data: Mapping):
        return cls(**data)


@dataclass
class EduidTestResultPayload(Payload):
    """Some statistics for source/sink test runs"""

    counter: int
    first_ts: datetime
    last_ts: datetime
    delta: str  # bson can't encode timedelta
    per_second: int

    @classmethod
    def from_dict(cls, data: Mapping):
        return cls(**data)


@dataclass
class EduidSCIMAPINotification(Payload):
    data_owner: str
    post_url: str
    message: str

    @classmethod
    def from_dict(cls, data: Mapping):
        data = dict(data)  # Do not change caller data
        return cls(**data)


@dataclass
class EmailPayload(Payload):
    email: str
    reference: str
    language: str

    @classmethod
    def from_dict(cls, data: Mapping):
        data = dict(data)  # Do not change caller data
        return cls(**data)


@dataclass
class EduidInviteEmail(EmailPayload):
    invite_link: str
    invite_code: str
    inviter_name: str
    version: int = 1


@dataclass
class EduidSignupEmail(EmailPayload):
    verification_code: str
    site_name: str
    version: int = 1


@dataclass
class OldEduidSignupEmail(EmailPayload):
    verification_link: str
    site_name: str
    site_url: str
    version: int = 1
