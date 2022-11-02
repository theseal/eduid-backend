#!/usr/bin/python
#
# Copyright (c) 2014 NORDUnet A/S
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
import base64
import ipaddress
import logging
from enum import Enum
from typing import Union

from eduid.userdb.idp import IdPUser

logger = logging.getLogger(__name__)


def b64encode(source: Union[str, bytes]) -> str:
    if isinstance(source, str):
        _source = bytes(source, "utf-8")
    else:
        _source = source
    return base64.b64encode(_source).decode("utf-8")


def maybe_xml_to_string(message: Union[str, bytes]) -> str:
    """
    Try to parse message as an XML string, and then return it pretty-printed.

    If message couldn't be parsed, return string representation of it instead.

    This is used to (debug-)log SAML requests/responses in a readable way.

    :param message: XML string typically
    :return: something ready for logging
    """
    if isinstance(message, bytes):
        # message is returned as binary from pysaml2 in python3
        message = message.decode("utf-8")
    try:
        from defusedxml import ElementTree as DefusedElementTree

        parser = DefusedElementTree.DefusedXMLParser()
        xml = DefusedElementTree.XML(message, parser)
        _xml = DefusedElementTree.tostring(xml)
        if not isinstance(_xml, bytes):
            # how odd for a function called tostring to not return a string...
            raise ValueError("DefusedElementTree.tostring() did not return bytes")
        return _xml.decode("utf-8")
    except Exception:
        logger.exception(f"Could not parse message of type {type(message)!r} as XML")
        return message


class IPProximity(str, Enum):
    SAME = "SAME"
    NEAR = "NEAR"
    FAR = "FAR"


def get_ip_proximity(a: str, b: str) -> IPProximity:
    """Tell how far apart IP A and B are.

    The addresses are either deemed to be 'SAME', 'NEAR' or 'FAR' apart.

    The definition of NEAR is /16 for IPv4 and /48 for IPv6.
    """
    ip_a = ipaddress.ip_address(a)
    ip_b = ipaddress.ip_address(b)
    logger.debug(f"Checking proximity of IP {ip_a} and {ip_b}")
    logger.debug(f"Checking proximity of IP {ip_a!r} and {ip_b!r}")
    if ip_a == ip_b:
        logger.debug(f"IP addresses {ip_a} and {ip_b} deemed to be SAME")
        return IPProximity.SAME
    if isinstance(ip_a, ipaddress.IPv4Address) and isinstance(ip_a, ipaddress.IPv4Address):
        net_a = ipaddress.ip_network(str(ip_a) + "/16", strict=False)
        if ip_b in net_a:
            logger.debug(f"IP addresses {ip_a} and {ip_b} deemed to be NEAR")
            return IPProximity.NEAR
    if isinstance(ip_a, ipaddress.IPv6Address) and isinstance(ip_a, ipaddress.IPv6Address):
        net_a = ipaddress.ip_network(str(ip_a) + "/48", strict=False)
        if ip_b in net_a:
            logger.debug(f"IP addresses {ip_a} and {ip_b} deemed to be NEAR")
            return IPProximity.NEAR
    logger.debug(f"IP addresses {ip_a} and {ip_b} deemed to be FAR")
    return IPProximity.FAR


def get_login_username(user: IdPUser) -> str:
    """From a user, get the username that would map back to this user if someone enters it in the login process."""
    if user.mail_addresses.primary:
        # Provide e-mail from (potentially expired) SSO session to frontend, so it can populate
        # the username field for the user
        _mail = user.mail_addresses.primary.email
        return _mail
    elif user.phone_numbers.primary:
        _phone = user.phone_numbers.primary.number
        return _phone

    # TODO: Also support NIN and other 'external identifiers' as username?
    return user.eppn
