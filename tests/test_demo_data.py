"""The committed demo pre-aggregates must reproduce the SQL headline KPIs exactly.

kpi_reference.json is written from reporting.vw_executive_summary by the same export
run that writes the parquet files, so these tests catch any drift between the demo's
re-aggregation and the warehouse definitions.
"""
from __future__ import annotations

import json

import pandas as pd
import pytest

from olist_bi.export_demo import DEMO_DATA_DIR

if not (DEMO_DATA_DIR / "kpi_reference.json").exists():
    pytest.skip("demo data not exported yet (python -m olist_bi export)", allow_module_level=True)

REFERENCE = json.loads((DEMO_DATA_DIR / "kpi_reference.json").read_text(encoding="utf-8"))
ORDERS = pd.read_parquet(DEMO_DATA_DIR / "orders.parquet")
VALID = ORDERS[ORDERS["is_valid_order"]]


def test_reference_matches_documented_headline_kpis():
    # Values published in the README / CV; a change here means the metric definitions moved.
    assert REFERENCE["net_revenue"] == pytest.approx(13_494_400.74)
    assert REFERENCE["total_orders"] == 98_207
    assert REFERENCE["total_customers"] == 96_096
    assert REFERENCE["avg_order_value"] == pytest.approx(137.41)


def test_demo_net_revenue_and_orders():
    assert VALID["revenue"].sum() == pytest.approx(REFERENCE["net_revenue"], abs=0.01)
    assert VALID["orders"].sum() == REFERENCE["total_orders"]
    assert VALID["freight"].sum() == pytest.approx(REFERENCE["total_freight"], abs=0.01)


def test_demo_gross_revenue_includes_canceled():
    assert ORDERS["revenue"].sum() == pytest.approx(REFERENCE["gross_revenue"], abs=0.01)


def test_demo_delivery_and_review_kpis():
    late_rate = 100 * ORDERS["late_orders"].sum() / ORDERS["valid_delivery_orders"].sum()
    assert round(late_rate, 2) == pytest.approx(REFERENCE["late_delivery_rate_pct"])
    avg_days = ORDERS["delivery_days_sum"].sum() / ORDERS["delivery_days_n"].sum()
    assert round(avg_days, 1) == pytest.approx(REFERENCE["avg_delivery_days"])
    avg_review = ORDERS["review_sum"].sum() / ORDERS["review_n"].sum()
    assert round(avg_review, 2) == pytest.approx(REFERENCE["avg_review_score"])


@pytest.mark.parametrize("name", ["categories", "sellers"])
def test_item_grain_tables_reconcile_to_net_revenue(name):
    frame = pd.read_parquet(DEMO_DATA_DIR / f"{name}.parquet")
    assert frame["revenue"].sum() == pytest.approx(REFERENCE["net_revenue"], abs=0.01)


def test_delivery_buckets_cover_every_order_with_a_late_flag():
    buckets = pd.read_parquet(DEMO_DATA_DIR / "delivery_buckets.parquet")
    late = buckets[buckets["delay_bucket"] != "0. On time or early"]["orders"].sum()
    assert late == ORDERS["late_orders"].sum()
