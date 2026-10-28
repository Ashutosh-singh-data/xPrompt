from pathlib import Path
from typing import List, Union
import json
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base backend directory
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_FILE = (BACKEND_DIR / "data" / "consultos.db").resolve()


class Settings(BaseSettings):
    """ConsultOS backend application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "ConsultOS Backend"
    API_PREFIX: str = "/api"
    DEBUG: bool = False

    # Default SQLite URL with an absolute, predictable path
    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_FILE.as_posix()}"

    # CORS configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v_stripped = v.strip()
            if v_stripped.startswith("[") and v_stripped.endswith("]"):
                try:
                    return json.loads(v_stripped)
                except Exception:
                    pass
            return [i.strip() for i in v_stripped.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []

    def ensure_db_directories(self) -> None:
        """Ensure parent directories exist for local SQLite database file."""
        if self.DATABASE_URL.startswith("sqlite:///"):
            # Strip sqlite:/// to get filesystem path
            raw_path = self.DATABASE_URL.replace("sqlite:///", "")
            if raw_path and raw_path != ":memory:":
                db_path = Path(raw_path)
                db_path.parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_db_directories()
