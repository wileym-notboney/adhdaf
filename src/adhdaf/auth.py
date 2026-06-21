# ABOUTME: Bearer token authentication for API endpoints.
# ABOUTME: Two tiers — capture token (for intake) and admin token (for management).
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from adhdaf.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


async def require_capture_token(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> str:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    token = credentials.credentials
    if token not in (settings.capture_token, settings.admin_token):
        raise HTTPException(status_code=403, detail="Invalid token")
    return token


async def require_admin_token(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> str:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    if credentials.credentials != settings.admin_token:
        raise HTTPException(status_code=403, detail="Admin token required")
    return credentials.credentials


CaptureAuth = Depends(require_capture_token)
AdminAuth = Depends(require_admin_token)
