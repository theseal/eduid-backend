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

from __future__ import absolute_import

import imp
import time
import six
from hashlib import sha256
from saml2.config import SPConfig
from pwgen import pwgen
from nacl import secret, encoding
import nacl.exceptions

from eduid_common.api.utils import urlappend

import logging
logger = logging.getLogger(__name__)


def get_saml2_config(module_path):

    module = imp.load_source('saml2_settings', module_path)

    conf = SPConfig()
    conf.load(module.SAML_CONFIG)
    return conf


def get_location(http_info):
    """Extract the redirect URL from a pysaml2 http_info object"""
    assert 'headers' in http_info
    headers = http_info['headers']

    assert len(headers) == 1
    header_name, header_value = headers[0]
    assert header_name == 'Location'
    return header_value


def get_saml_attribute(session_info, attr_name):
    """
    Get value from a SAML attribute received from the SAML IdP.

    session_info is a pysaml2 response.session_info(). This is a dictionary like
        {'mail': ['user@example.edu'],
         'eduPersonPrincipalName': ['gadaj-fifib@idp.example.edu']
      }

    :param session_info: SAML attributes received by pysaml2 client.
    :param attr_name: The attribute to look up
    :returns: Attribute values

    :type session_info: dict()
    :type attr_name: string()
    :rtype: [string()]
    """
    if not 'ava' in session_info:
        raise ValueError('SAML attributes (ava) not found in session_info')

    attributes = session_info['ava']

    logger.debug('SAML attributes received: %s' % attributes)

    attr_name = attr_name.lower()
    # Look for the canonicalized attribute in the SAML assertion attributes
    for saml_attr, local_fields in attributes.items():
        if saml_attr.lower() == attr_name:
            return attributes[saml_attr]


def no_authn_views(app, paths):
    """
    :param app: Flask app
    :type app: flask.Flask
    :param paths: Paths that does not require authentication
    :type paths: list

    :return: Flask app
    :rtype: flask.Flask
    """
    app_root = app.config.get('APPLICATION_ROOT')
    if app_root is None:
        app_root = ''
    for path in paths:
        no_auth_regex = '^{!s}$'.format(urlappend(app_root, path))
        if no_auth_regex not in app.config['NO_AUTHN_URLS']:
            app.config['NO_AUTHN_URLS'].append(no_auth_regex)
    return app


def generate_password(length=12):
    return pwgen(int(length), no_capitalize=True, no_symbols=True)


def generate_auth_token(shared_key, usage, data, ts=None):
    """
    Generate tokens that can be sent to one eduID app to another, using a
    shared secret.

    :param shared_key: The shared secret
    :param usage: The intended usage of this token
    :param data: Protected data
    :param ts: Timestamp when the token is minted

    :return: An encrypted and protected token, safe to put in an URL
    """
    if ts is None:
        ts = int(time.time())
    timestamp = '{:x}'.format(ts)
    token_data = '{}|{}|{}'.format(usage, timestamp, data).encode('ascii')
    box = secret.SecretBox(encoding.URLSafeBase64Encoder.decode(shared_key.encode('ascii')))
    encrypted = box.encrypt(token_data)
    b64 = encoding.URLSafeBase64Encoder.encode(encrypted)
    if six.PY2:
        return b64, timestamp
    return b64.decode('utf-8'), timestamp


def verify_auth_token(shared_key, eppn, token, timestamp, usage, generator=sha256):
    """
    Authenticate a user with a token.

    Used after signup or for idp actions.

    Authentication is done using a shared key in the configuration of the
    authn and signup applications or another shared key in the configuration of idp and actions.

    :param shared_key: Applications shared key
    :param eppn: the identifier of the user as string
    :param token: authentication token as string
    :param timestamp: unixtime of signup application as hex string
    :param usage: The intended usage of the token, to safeguard against tokens being maliciously
                  sent to another token consumer than intended
    :param generator: hash function to use (default: SHA-256)
    :return: bool, True on valid authentication
    """
    logger.debug('Trying to authenticate user {} with auth token {!r}'.format(eppn, token))
    if six.PY2:
        shared_key = shared_key.encode('ascii')

    # check timestamp to make sure it is within -300..900 seconds from now
    now = int(time.time())
    ts = int(timestamp, 16)
    if (ts < now - 300) or (ts > now + 900):
        logger.debug('Auth token timestamp {} out of bounds ({} seconds from {})'.format(
            timestamp, ts - now, now))
        return False

    # try to open secret box
    try:
        box = secret.SecretBox(encoding.URLSafeBase64Encoder.decode(shared_key))
        plaintext = box.decrypt(token.encode('ascii'), encoder=encoding.URLSafeBase64Encoder)
        expected = '{}|{}|{}'.format(usage, timestamp, eppn).encode('ascii')
        logger.debug('Comparing plaintext {!r} with expected {!r}'.format(plaintext, expected))
        return plaintext == expected
    except (LookupError,  ValueError, nacl.exceptions.CryptoError) as e:
        logger.debug('Secretbox decryption failed, error: ' + str(e))
        return False

