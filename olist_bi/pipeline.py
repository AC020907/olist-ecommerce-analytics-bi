"""Full rebuild of the warehouse: reset -> raw load -> staging -> dimensions -> facts -> reporting views.

The whole build runs in a single transaction, so a failure at any step leaves the
previously built model untouched instead of a half-dropped schema.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

import psycopg

from .config import SQL_DIR

log = logging.getLogger(__name__)

# Order matters: raw tables carry FK constraints (orders -> customers, items -> products/sellers, ...).
RAW_FILES: list[tuple[str, str]] = [
    ("raw.customers", "olist_customers_dataset.csv"),
    ("raw.products", "olist_products_dataset.csv"),
    ("raw.sellers", "olist_sellers_dataset.csv"),
    ("raw.product_category_name_translation", "product_category_name_translation.csv"),
    ("raw.geolocation", "olist_geolocation_dataset.csv"),
    ("raw.orders", "olist_orders_dataset.csv"),
    ("raw.order_items", "olist_order_items_dataset.csv"),
    ("raw.order_payments", "olist_order_payments_dataset.csv"),
    ("raw.order_reviews", "olist_order_reviews_dataset.csv"),
]

SCHEMA_LAYERS = ["00_reset", "01_schema"]
MODEL_LAYERS = ["03_cleaning", "04_dimensions", "05_facts", "06_reporting_views"]


def sql_files(layer: str, sql_dir: Path = SQL_DIR) -> list[Path]:
    files = sorted((sql_dir / layer).glob("*.sql"))
    if not files:
        raise FileNotFoundError(f"No SQL files found in {sql_dir / layer}")
    return files


def run_sql_file(conn: psycopg.Connection, path: Path) -> None:
    started = time.perf_counter()
    conn.execute(path.read_text(encoding="utf-8"))
    log.info("  %-55s %6.2fs", path.relative_to(path.parents[1]).as_posix(), time.perf_counter() - started)


def check_raw_files(data_dir: Path) -> None:
    missing = [name for _, name in RAW_FILES if not (data_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing raw CSV files in {data_dir}: {', '.join(missing)}")


def load_raw(conn: psycopg.Connection, data_dir: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    with conn.cursor() as cur:
        cur.execute("SET client_encoding = 'UTF8'")
        for table, filename in RAW_FILES:
            started = time.perf_counter()
            with cur.copy(f"COPY {table} FROM STDIN WITH (FORMAT csv, HEADER true)") as copy:
                with open(data_dir / filename, "rb") as fh:
                    while chunk := fh.read(1 << 20):
                        copy.write(chunk)
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cur.fetchone()[0]
            log.info("  load %-45s %9d rows %6.2fs", table, counts[table], time.perf_counter() - started)
    return counts


def build(database_url: str, data_dir: Path) -> dict[str, int]:
    """Rebuild every schema from the raw CSVs. Safe to run repeatedly."""
    check_raw_files(data_dir)
    started = time.perf_counter()
    with psycopg.connect(database_url) as conn:
        # Suppress the 'does not exist, skipping' NOTICE noise from DROP ... IF EXISTS.
        conn.execute("SET client_min_messages = warning")
        for layer in SCHEMA_LAYERS:
            log.info("[%s]", layer)
            for path in sql_files(layer):
                run_sql_file(conn, path)
        log.info("[raw load] from %s", data_dir)
        counts = load_raw(conn, data_dir)
        for layer in MODEL_LAYERS:
            log.info("[%s]", layer)
            for path in sql_files(layer):
                run_sql_file(conn, path)
        conn.commit()
    log.info("Build finished in %.1fs", time.perf_counter() - started)
    return counts
