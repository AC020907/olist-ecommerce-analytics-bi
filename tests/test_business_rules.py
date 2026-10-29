"""Integration tests: build the warehouse from the fixture dataset and assert each business rule."""
from __future__ import annotations

from decimal import Decimal

import pytest

from fixture_data import EXPECTED, OA, OB, OC, OD, OF, P2, P3, S1, S2, U1, U3

pytestmark = pytest.mark.integration


def scalar(query, sql):
    return query(sql)[0][0]


def test_executive_summary_matches_hand_computed_values(query):
    row = query(
        "SELECT total_orders, total_customers, net_revenue, gross_revenue, avg_order_value, "
        "total_freight, late_delivery_rate_pct FROM reporting.vw_executive_summary"
    )[0]
    assert row == (
        EXPECTED["valid_orders"],
        EXPECTED["customers"],
        Decimal("330.00"),
        Decimal("530.00"),
        Decimal("82.50"),
        Decimal("33.00"),
        Decimal("33.33"),
    )


def test_multi_item_multi_payment_order_does_not_fan_out(query):
    items_revenue, freight, payments, n_items = query(
        f"SELECT items_revenue, freight_total, payments_total, n_items FROM analytics.fact_orders WHERE order_id = '{OA}'"
    )[0]
    assert (items_revenue, freight, payments, n_items) == (Decimal("150.00"), Decimal("15.00"), Decimal("165.00"), 2)


def test_fact_tables_keep_source_grain(query):
    assert scalar(query, "SELECT COUNT(*) FROM analytics.fact_orders") == EXPECTED["orders_total"]
    assert scalar(query, "SELECT COUNT(*) FROM analytics.fact_order_items") == 6
    assert scalar(query, "SELECT COUNT(*) FROM analytics.fact_payments") == 6


def test_canceled_and_unavailable_orders_excluded_from_net(query):
    net_items = scalar(
        query,
        "SELECT SUM(price) FROM analytics.fact_order_items WHERE order_status NOT IN ('canceled', 'unavailable')",
    )
    assert net_items == Decimal("330.00")


def test_impossible_delivery_dates_produce_no_delivery_kpis(query):
    row = query(
        f"SELECT has_valid_delivery_dates, delivery_days, is_late FROM analytics.fact_orders WHERE order_id = '{OD}'"
    )[0]
    assert row == (False, None, None)


def test_late_order_flag_and_multi_review_average(query):
    is_late, review_count, avg_review = query(
        f"SELECT is_late, review_count, avg_review_score FROM analytics.fact_orders WHERE order_id = '{OB}'"
    )[0]
    assert is_late is True
    assert review_count == 2
    assert avg_review == Decimal("2")


def test_customer_identity_uses_unique_id_and_latest_address(query):
    lifetime, is_repeat, state = query(
        f"SELECT lifetime_order_count, is_repeat_customer, state FROM analytics.dim_customer WHERE customer_unique_id = '{U1}'"
    )[0]
    assert (lifetime, is_repeat, state) == (2, True, "RJ")
    assert scalar(query, "SELECT COUNT(*) FROM analytics.dim_customer WHERE is_repeat_customer") == EXPECTED["repeat_customers"]


def test_category_fallbacks_are_explicit(query):
    rows = dict(
        (pid, (name, flag))
        for pid, name, flag in query("SELECT product_id, category_name_en, category_data_quality FROM analytics.dim_product")
    )
    assert rows[P2] == ("unknown", "missing_category")
    assert rows[P3] == ("categoria_sem_traducao", "missing_translation")


def test_geolocation_collapses_to_one_trimmed_row_per_zip(query):
    assert query("SELECT city, state FROM analytics.dim_geography WHERE zip_code_prefix = '01001'") == [("sao paulo", "SP")]


def test_unmapped_zip_kept_in_unknown_bucket_so_geography_reconciles(query):
    rows = dict(query("SELECT state, revenue FROM reporting.vw_customer_geography_performance"))
    assert rows["Unknown"] == Decimal("40.00")
    assert sum(rows.values()) == Decimal("330.00")
    assert scalar(query, f"SELECT COUNT(*) FROM analytics.dim_customer WHERE customer_unique_id = '{U3}'") == 1


def test_category_and_seller_views_reconcile_to_net_revenue(query):
    categories = dict(query("SELECT category_name_en, revenue FROM reporting.vw_category_performance"))
    assert categories == {"health_beauty": Decimal("240.00"), "unknown": Decimal("90.00")}
    sellers = dict(query("SELECT seller_id, revenue FROM reporting.vw_seller_performance"))
    assert sellers == {S1: Decimal("240.00"), S2: Decimal("90.00")}


def test_all_error_level_quality_checks_pass(built_db):
    from olist_bi.quality import run_checks

    failures = [r for r in run_checks(built_db) if r.status == "FAIL"]
    assert not failures, [(r.check.name, r.value) for r in failures]


def test_rebuild_is_idempotent(built_db, fixture_data_dir, query):
    from olist_bi.pipeline import build

    before = query("SELECT * FROM reporting.vw_executive_summary")
    build(built_db, fixture_data_dir)
    assert query("SELECT * FROM reporting.vw_executive_summary") == before
    assert scalar(query, "SELECT COUNT(*) FROM raw.orders") == EXPECTED["orders_total"]


def test_delivery_on_promised_day_is_on_time(query):
    # Delivered 18:00 on the promised calendar date: a timestamp comparison would call it late.
    assert query(f"SELECT is_late FROM analytics.fact_orders WHERE order_id = '{OF}'") == [(False,)]


def test_canceled_order_with_delivery_dates_is_outside_late_rate(query):
    has_valid, is_late = query(
        f"SELECT has_valid_delivery_dates, is_late FROM analytics.fact_orders WHERE order_id = '{OC}'"
    )[0]
    assert (has_valid, is_late) == (True, None)
    assert scalar(query, "SELECT COUNT(*) FROM analytics.fact_orders WHERE is_late IS NOT NULL") == 3
