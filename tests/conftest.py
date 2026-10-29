from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fixture_data import write_fixture_csvs  # noqa: E402


def _test_database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL not set; integration tests need a disposable PostgreSQL database")
    database = urlparse(url).path.lstrip("/")
    # The build drops the raw/staging/analytics/reporting schemas, so refuse anything that
    # doesn't look like a throwaway database.
    if "test" not in database:
        pytest.exit(f"Refusing to run destructive tests against database '{database}' (name must contain 'test')")
    return url


@pytest.fixture(scope="session")
def test_db_url() -> str:
    return _test_database_url()


@pytest.fixture(scope="session")
def fixture_data_dir(tmp_path_factory) -> Path:
    return write_fixture_csvs(tmp_path_factory.mktemp("olist_raw"))


@pytest.fixture(scope="session")
def built_db(test_db_url, fixture_data_dir) -> str:
    from olist_bi.pipeline import build

    build(test_db_url, fixture_data_dir)
    return test_db_url


@pytest.fixture
def query(built_db):
    import psycopg

    def run(sql: str):
        with psycopg.connect(built_db) as conn:
            return conn.execute(sql).fetchall()

    return run
