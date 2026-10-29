from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = REPO_ROOT / "sql"
DEFAULT_DATA_DIR = REPO_ROOT / "data" / "raw"

try:
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")
except ImportError:  # python-dotenv is optional; plain env vars still work
    pass


@dataclass(frozen=True)
class Settings:
    database_url: str
    data_dir: Path


def build_database_url(env: dict[str, str] | None = None) -> str:
    """DATABASE_URL wins; otherwise assemble one from the standard libpq PG* variables."""
    env = dict(os.environ) if env is None else env
    if env.get("DATABASE_URL"):
        return env["DATABASE_URL"]
    host = env.get("PGHOST", "localhost")
    port = env.get("PGPORT", "5432")
    user = env.get("PGUSER", "postgres")
    database = env.get("PGDATABASE", "olist_analytics")
    # Password is deliberately left out of the URL: libpq reads PGPASSWORD / .pgpass itself.
    return f"postgresql://{user}@{host}:{port}/{database}"


def get_settings(env: dict[str, str] | None = None) -> Settings:
    env = dict(os.environ) if env is None else env
    data_dir = Path(env.get("OLIST_DATA_DIR", str(DEFAULT_DATA_DIR)))
    return Settings(database_url=build_database_url(env), data_dir=data_dir)
