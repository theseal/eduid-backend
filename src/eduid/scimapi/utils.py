import base64
import logging
from typing import AnyStr
from uuid import uuid4

from bson import ObjectId
from jwcrypto import jwk

from eduid.common.config.exceptions import BadConfiguration
from eduid.scimapi.config import ScimApiConfig

logger = logging.getLogger(__name__)


def b64_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("utf-8").strip("=")


def b64_decode(data: AnyStr) -> bytes:
    if isinstance(data, str):
        _data = data.encode("utf-8")
    elif isinstance(data, bytes):
        _data = data
    else:
        raise ValueError("b64_decode needs either str or bytes")
    _data += b"=" * (len(_data) % 4)
    return base64.urlsafe_b64decode(_data)


def filter_none(x):
    """
    Recursively removes key, value pairs or items that is None.
    """
    if isinstance(x, dict):
        return {k: filter_none(v) for k, v in x.items() if v is not None}
    elif isinstance(x, list):
        return [filter_none(i) for i in x if x is not None]
    else:
        return x


def make_etag(version: ObjectId):
    return f'W/"{version}"'


def get_unique_hash():
    return str(uuid4())


def get_short_hash(entropy=10):
    return uuid4().hex[:entropy]


def load_jwks(config: ScimApiConfig) -> jwk.JWKSet:
    if not config.keystore_path.exists():
        raise BadConfiguration(f"JWKS path {config.keystore_path} does not exist.")
    with config.keystore_path.open("r") as f:
        jwks = jwk.JWKSet.from_json(f.read())
        logger.info(f"jwks loaded from {config.keystore_path}")
    return jwks
