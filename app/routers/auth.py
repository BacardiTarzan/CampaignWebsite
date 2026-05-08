from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from ..config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

_config = Config(environ={
    "GOOGLE_CLIENT_ID": settings.google_client_id,
    "GOOGLE_CLIENT_SECRET": settings.google_client_secret,
})
oauth = OAuth(_config)
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

_ALLOWED = {e.strip().lower() for e in settings.allowed_emails.split(",") if e.strip()}


@router.get("/login")
async def login(request: Request):
    redirect_uri = str(request.url_for("auth_callback"))
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback", name="auth_callback")
async def callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    if not user_info:
        return JSONResponse({"error": "No user info returned from Google"}, status_code=400)

    email = (user_info.get("email") or "").lower()
    if _ALLOWED and email not in _ALLOWED:
        return JSONResponse({"error": "Access denied. Your email is not on the invite list."}, status_code=403)

    request.session["user"] = {
        "email": email,
        "name": user_info.get("name", email),
        "picture": user_info.get("picture", ""),
    }
    return RedirectResponse("/")


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/auth/login")


@router.get("/me")
async def me(request: Request):
    user = request.session.get("user")
    if not user:
        return JSONResponse({"error": "Not authenticated"}, status_code=401)
    return user
