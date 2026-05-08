import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pathlib import Path
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .config import settings
from .database import engine, SessionLocal
from .models import *  # noqa: F401, F403 — ensures all models are registered
from .database import Base
from .routers import content, characters, admin
from .routers.auth import router as auth_router
from .services.seeder import seed_all

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        from .models.content import Species
        if db.query(Species).count() == 0:
            log.info("Database empty — seeding from reference/...")
            counts = seed_all(db)
            log.info("Seed complete: %s", counts)
        else:
            log.info("Database already seeded, skipping.")
    except Exception as e:
        log.error("Seeding failed: %s", e)
    finally:
        db.close()
    yield


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        proto = request.headers.get("x-forwarded-proto")
        if proto == "http":
            url = request.url.replace(scheme="https")
            return RedirectResponse(url, status_code=301)
        return await call_next(request)


app = FastAPI(title="D&D 2024 Character Generator", lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=settings.session_secret)
app.add_middleware(HTTPSRedirectMiddleware)

app.include_router(auth_router)
app.include_router(content.router)
app.include_router(characters.router)
app.include_router(admin.router)

static_path = Path(settings.static_dir)
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/")
def serve_index():
    return FileResponse(str(static_path / "index.html"))


@app.get("/admin")
def serve_admin():
    return FileResponse(str(static_path / "admin.html"))
