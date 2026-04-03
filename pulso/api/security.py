"""Admin endpoint security: Bearer token validation."""
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from pulso.config import settings

_bearer = HTTPBearer(auto_error=False)


def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> str:
    """
    Dependency that enforces Bearer token auth for admin endpoints.
    Raises 401 if token is missing or wrong.
    """
    if credentials is None or credentials.credentials != settings.admin_secret:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized — invalid or missing Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials
