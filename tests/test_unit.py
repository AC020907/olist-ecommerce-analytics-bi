"""Fast tests that need no database."""
from __future__ import annotations

import pytest

from olist_bi.config import build_database_url, get_settings
from olist_bi.pipeline import MODEL_LAYERS, RAW_FILES, SCHEMA_LAYERS, check_raw_files, sql_files
from olist_bi.quality import CHECKS, Check, CheckResult, format_report


def test_database_url_prefers_explicit_url():
    assert build_database_url({"DATABASE_URL": "postgresql://a@b:1/c", "PGHOST": "x"}) == "postgresql://a@b:1/c"


def test_database_url_built_from_pg_vars_without_password():
    url = build_database_url({"PGHOST": "db", "PGPORT": "5433", "PGUSER": "bi", "PGPASSWORD": "secret"})
    assert url == "postgresql://bi@db:5433/olist_analytics"
    assert "secret" not in url


def test_data_dir_overridable(tmp_path):
    assert get_settings({"OLIST_DATA_DIR": str(tmp_path)}).data_dir == tmp_path


@pytest.mark.parametrize("layer", SCHEMA_LAYERS + MODEL_LAYERS)
def test_every_pipeline_layer_has_sql_files(layer):
    files = sql_files(layer)
    assert [f.name for f in files] == sorted(f.name for f in files)


def test_pipeline_sql_has_no_psql_meta_commands():
    # The Python runner sends files straight to the server, so psql-only syntax would break it.
    for layer in SCHEMA_LAYERS + MODEL_LAYERS:
        for path in sql_files(layer):
            assert not any(line.lstrip().startswith("\\") for line in path.read_text(encoding="utf-8").splitlines()), path


def test_raw_files_cover_every_raw_table():
    assert len(RAW_FILES) == 9
    assert len({table for table, _ in RAW_FILES}) == 9


def test_missing_raw_file_is_reported(tmp_path):
    with pytest.raises(FileNotFoundError, match="olist_orders_dataset.csv"):
        check_raw_files(tmp_path)


def test_check_names_are_unique():
    names = [c.name for c in CHECKS]
    assert len(names) == len(set(names))


def test_check_status_respects_severity_and_tolerance():
    error = Check("e", "c", "d", "SELECT 1")
    warn = Check("w", "c", "d", "SELECT 1", severity="warn", tolerance=0.1)
    assert CheckResult(error, 0).status == "PASS"
    assert CheckResult(error, 1).status == "FAIL"
    assert CheckResult(warn, 0.05).status == "PASS"
    assert CheckResult(warn, 0.5).status == "WARN"


def test_report_summarises_counts():
    results = [CheckResult(Check("a", "c", "d", "x"), 0), CheckResult(Check("b", "c", "d", "x"), 3)]
    report = format_report(results)
    assert "1 passed, 0 warnings, 1 failed" in report
    assert "| FAIL |" in report
