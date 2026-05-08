from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    database_url: str = f"sqlite:///{BASE_DIR}/campaign.db"
    reference_dir: str = str(BASE_DIR / "reference")
    static_dir: str = str(BASE_DIR / "static")
    templates_dir: str = str(BASE_DIR / "app" / "templates")
    debug: bool = False

    google_client_id: str = ""
    google_client_secret: str = ""
    session_secret: str = "dev-secret"
    allowed_emails: str = ""   # comma-separated
    admin_email: str = ""

    model_config = {"env_file": str(BASE_DIR / ".env"), "extra": "ignore"}


settings = Settings()
