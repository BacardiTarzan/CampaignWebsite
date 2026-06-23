import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pathlib import Path
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command

from .config import settings
from .database import SessionLocal, engine
from .models import *  # noqa: F401, F403 — ensures all models are registered
from .routers import content, characters, admin
from .routers.auth import router as auth_router
from .routers.encounter import router as encounter_router, ws_router as encounter_ws_router
from .services.seeder import seed_all

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def _seed():
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    from .database import Base
    from sqlalchemy import text

    alembic_ini = Path(__file__).resolve().parent.parent / "alembic.ini"
    alembic_cfg = AlembicConfig(str(alembic_ini))

    # Step 1: create all tables from models (idempotent, checkfirst=True by default).
    # This must happen before alembic runs so add_column migrations don't fail on
    # tables that don't exist yet (the initial schema migration is intentionally empty).
    try:
        Base.metadata.create_all(bind=engine)
        log.info("create_all complete.")
    except Exception as e:
        log.error("create_all failed: %s", e, exc_info=True)

    # Step 2: if this is a fresh DB (alembic_version empty or missing), stamp to head
    # so alembic doesn't try to add columns that create_all already created.
    # For existing DBs with partial migrations, run upgrade normally.
    try:
        with engine.connect() as conn:
            try:
                version_count = conn.execute(
                    text("SELECT count(*) FROM alembic_version")
                ).scalar()
            except Exception:
                version_count = 0

        if version_count == 0:
            alembic_command.stamp(alembic_cfg, "head")
            log.info("Fresh DB: stamped alembic to head.")
        else:
            alembic_command.upgrade(alembic_cfg, "head")
            log.info("Alembic migrations applied.")
    except Exception as e:
        log.error("Alembic failed: %s", e, exc_info=True)

    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _seed)
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
app.include_router(encounter_router)
app.include_router(encounter_ws_router)

static_path = Path(settings.static_dir)
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/")
def serve_landing():
    return FileResponse(str(static_path / "landing.html"))


@app.get("/charactercreator")
def serve_index():
    return FileResponse(str(static_path / "index.html"))


@app.get("/admin")
def serve_admin():
    return FileResponse(str(static_path / "admin.html"))


@app.get("/portal")
def serve_portal():
    return FileResponse(str(static_path / "portal.html"))


@app.get("/lore")
def serve_lore():
    return FileResponse(str(static_path / "lore.html"))


@app.get("/glossary")
def serve_glossary():
    return FileResponse(str(static_path / "glossary.html"))


@app.get("/characters/{char_id}/sheet")
def serve_sheet(char_id: int):
    return FileResponse(str(static_path / "sheet.html"))


@app.get("/characters/{char_id}/levelup")
def serve_levelup(char_id: int):
    return FileResponse(str(static_path / "levelup.html"))


@app.get("/encounter")
def serve_encounter():
    return FileResponse(str(static_path / "encounter.html"))
