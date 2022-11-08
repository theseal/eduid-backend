import json
import logging
from typing import List

from fastapi import Request, Response, status
from jwcrypto import jwt
from jwcrypto.common import JWException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse

from eduid.workers.amapi.context_request import ContextRequestMixin

import fnmatch

from eduid.workers.amapi.utils import AuthnBearerToken

logger = logging.getLogger(__name__)


class AccessDenied(Exception):
    """Break out of get_data_owner when requested access (in the token) is not allowed"""

    pass


# middleware needs to return a response
# some background: https://github.com/tiangolo/fastapi/issues/458
def return_error_response(status_code: int, detail: str):
    return PlainTextResponse(status_code=status_code, content=detail)


class AuthenticationMiddleware(BaseHTTPMiddleware, ContextRequestMixin):
    async def dispatch(self, req: Request, call_next) -> Response:
        req = self.make_context_request(request=req)
        path = req.url.path.lstrip(req.app.config.application_root)
        method_path = f"{req.method.lower()}:{path}"

        if not path:
            return return_error_response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Path empty",
            )

        if self._is_no_auth_path(req, method_path):
            return await call_next(req)

        auth = req.headers.get("Authorization")
        if not auth:
            return return_error_response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No authentication header found",
            )

        token = auth[len("Bearer ") :]
        _jwt = jwt.JWT()
        try:
            _jwt.deserialize(token, req.app.jwks)
            claims = json.loads(_jwt.claims)
        except (JWException, KeyError, ValueError) as e:
            logger.info(f"Bearer token error: {e}")
            return return_error_response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Bearer token error",
            )

        token = AuthnBearerToken(**claims)
        logger.debug(f"Bearer token: {token}")

        if self._access_granted(req, token, method_path):
            return await call_next(req)
        mura = 1
        return return_error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Account {token.service_name} is not allowed access to {method_path}",
        )

    @staticmethod
    def _is_no_auth_path(req: Request, path: str) -> bool:
        return path in req.app.config.no_authn_urls

    def _access_granted(self, req: Request, token: AuthnBearerToken, path: str) -> bool:
        if token.service_name in req.app.config.user_restriction:
            return self.glob_match(req.app.config.user_restriction[token.service_name], path)
        return False

    @staticmethod
    def glob_match(endpoints: List[str], path: str) -> bool:
        for endpoint in endpoints:
            if fnmatch.fnmatch(path, endpoint):
                return True
        return False
