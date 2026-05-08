from fastapi import Depends, HTTPException, Request
from .config import settings


def require_user(request: Request) -> dict:
    user = request.session.get("user")
    if not user:
        raise HTTPException(401, "Not authenticated")
    return user


def require_admin(user: dict = Depends(require_user)) -> dict:
    if user.get("email") != settings.admin_email:
        raise HTTPException(403, "Admin access required")
    return user
