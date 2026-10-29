"""Demo (pandas re-aggregation) vs. SQL (warehouse) KPI reconciliation under filters.

* fixture tests export the hand-built fixture warehouse and compare -- always run with TEST_DATABASE_URL.
* full-data tests compare the committed demo/data parquet files with a full warehouse built
  from data/raw -- run when OLIST_RECONCILE_DATABASE_URL points at one (CI does this).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "demo"))
import metrics as m  # noqa: E402

NET = "fo.order_status NOT IN ('canceled', 'unavailable')"

SQL_KPIS = f"""
SELECT
    COALESCE(SUM(fo.items_revenue) FILTER (WHERE {NET}), 0)                AS revenue,
    COALESCE(SUM(fo.items_revenue), 0)                                     AS gross_revenue,
    COUNT(*) FILTER (WHERE {NET})                                          AS orders,
    COALESCE(SUM(fo.freight_total) FILTER (WHERE {NET}), 0)                AS freight,
    AVG(fo.avg_review_score)                                               AS review,
    COUNT(*) FILTER (WHERE fo.is_late)                                     AS late_orders,
    100.0 * COUNT(*) FILTER (WHERE fo.is_late) / NULLIF(COUNT(fo.is_late), 0) AS late_pct,
    AVG(fo.delivery_days)                                                  AS delivery_days
FROM analytics.fact_orders fo
JOIN analytics.dim_date d       ON d.date_day = fo.order_date_key
JOIN analytics.dim_customer dc  ON dc.customer_unique_id = fo.customer_unique_id
LEFT JOIN analytics.dim_geography dg ON dg.zip_code_prefix = dc.zip_code_prefix
WHERE d.year_month BETWEEN %(month_from)s AND %(month_to)s
  AND (%(regions)s::text[] IS NULL OR COALESCE(dg.region, 'Unknown') = ANY(%(regions)s::text[]))
  AND (%(states)s::text[] IS NULL OR COALESCE(dg.state, 'Unknown') = ANY(%(states)s::text[]))
"""

FILTERS = {
    "all_months": ("2016-09", "2018-10", None, None),
    "analysis_window": ("2017-01", "2018-08", None, None),
    "h1_2018": ("2018-01", "2018-06", None, None),
    "region_nordeste": ("2016-09", "2018-10", ["Nordeste"], None),
    "region_unknown": ("2016-09", "2018-10", ["Unknown"], None),
    "state_sp_window": ("2017-01", "2018-08", None, ["SP"]),
    "two_states_one_month": ("2017-11", "2017-11", None, ["RJ", "MG"]),
}


def sql_kpis(url: str, month_from: str, month_to: str, regions, states) -> dict:
    with psycopg.connect(url) as conn:
        cur = conn.execute(SQL_KPIS, dict(month_from=month_from, month_to=month_to, regions=regions, states=states))
        return {c.name: (float(v) if v is not None else float("nan")) for c, v in zip(cur.description, cur.fetchone())}


def assert_kpis_match(demo: dict, sql: dict) -> None:
    assert demo["revenue"] == pytest.approx(sql["revenue"], abs=0.01)
    assert demo["gross_revenue"] == pytest.approx(sql["gross_revenue"], abs=0.01)
    assert demo["orders"] == sql["orders"]
    assert demo["freight"] == pytest.approx(sql["freight"], abs=0.01)
    assert demo["late_orders"] == sql["late_orders"]
    for key in ("review", "late_pct", "delivery_days"):
        assert demo[key] == pytest.approx(sql[key], rel=1e-9, nan_ok=True), key


# ---------------------------------------------------------------- fixture warehouse

@pytest.fixture(scope="module")
def fixture_export(built_db, tmp_path_factory):
    from olist_bi.export_demo import export

    out = tmp_path_factory.mktemp("demo_data")
    export(built_db, out)
    return out


@pytest.mark.integration
@pytest.mark.parametrize("name", ["all_months", "region_unknown"])
def test_fixture_demo_matches_sql(name, built_db, fixture_export):
    month_from, month_to, regions, states = FILTERS[name]
    orders = m.load_frames(fixture_export)["orders"]
    demo = m.kpis(m.apply_filters(orders, month_from, month_to, regions, states))
    assert_kpis_match(demo, sql_kpis(built_db, month_from, month_to, regions, states))


@pytest.mark.integration
def test_fixture_export_metadata(fixture_export):
    meta = m.load_json("export_metadata.json", fixture_export)
    assert (meta["first_order_date"], meta["last_order_date"]) == ("2017-03-10", "2017-06-01")


# ---------------------------------------------------------------- full dataset

@pytest.fixture(scope="module")
def full_db() -> str:
    url = os.environ.get("OLIST_RECONCILE_DATABASE_URL")
    if not url:
        pytest.skip("OLIST_RECONCILE_DATABASE_URL not set (needs a warehouse built from data/raw)")
    return url


@pytest.fixture(scope="module")
def frames():
    return m.load_frames()


@pytest.mark.parametrize("name", FILTERS)
def test_full_demo_matches_sql_under_filters(name, full_db, frames):
    month_from, month_to, regions, states = FILTERS[name]
    demo = m.kpis(m.apply_filters(frames["orders"], month_from, month_to, regions, states))
    assert_kpis_match(demo, sql_kpis(full_db, month_from, month_to, regions, states))


def test_full_empty_selection_has_no_orders(frames):
    empty = m.apply_filters(frames["orders"], "2016-09", "2016-09", ["Norte"], ["SP"])
    result = m.kpis(empty)
    assert result["orders"] == 0 and result["revenue"] == 0
    assert result["aov"] != result["aov"]  # NaN, rendered as "–" instead of a division error


def test_full_category_matches_sql_view(full_db, frames):
    cat = m.category_table(frames["categories"]).set_index("category")
    with psycopg.connect(full_db) as conn:
        rows = conn.execute(
            "SELECT category_name_en, revenue, items_sold, orders, avg_review_score FROM reporting.vw_category_performance"
        ).fetchall()
    assert len(rows) == len(cat)
    for name, revenue, items, orders, review in rows:
        demo = cat.loc[name.replace("_", " ")]
        assert demo["revenue"] == pytest.approx(float(revenue), abs=0.01)
        assert (demo["items"], demo["orders"]) == (items, orders)
        assert demo["review"] == pytest.approx(float(review), abs=0.0051)  # view rounds to 2 dp


def test_full_sellers_match_sql_view(full_db, frames):
    sel = m.seller_table(frames["sellers"]).set_index("seller_id")
    with psycopg.connect(full_db) as conn:
        rows = conn.execute(
            "SELECT seller_id, revenue, orders, late_delivery_rate_pct, avg_review_score "
            "FROM reporting.vw_seller_performance ORDER BY revenue DESC LIMIT 200"
        ).fetchall()
    for seller_id, revenue, orders, late_pct, review in rows:
        demo = sel.loc[seller_id]
        assert demo["revenue"] == pytest.approx(float(revenue), abs=0.01)
        assert demo["orders"] == orders
        if late_pct is not None:
            assert demo["late_pct"] == pytest.approx(float(late_pct), abs=0.0051)
        if review is not None:
            assert demo["review"] == pytest.approx(float(review), abs=0.0051)  # view rounds to 2 dp


def test_full_reference_matches_live_view(full_db):
    reference = m.load_json("kpi_reference.json")
    with psycopg.connect(full_db) as conn:
        cur = conn.execute("SELECT * FROM reporting.vw_executive_summary")
        live = {c.name: float(v) for c, v in zip(cur.description, cur.fetchone())}
    assert reference == pytest.approx(live)


CATEGORY_SQL = """
WITH cat_items AS (
    SELECT foi.order_id, foi.price
    FROM analytics.fact_order_items foi
    JOIN analytics.dim_product dp ON dp.product_id = foi.product_id
    JOIN analytics.dim_date d ON d.date_day = foi.order_date_key
    JOIN analytics.dim_customer dc ON dc.customer_unique_id = foi.customer_unique_id
    LEFT JOIN analytics.dim_geography dg ON dg.zip_code_prefix = dc.zip_code_prefix
    WHERE dp.category_name_en = %(category)s
      AND foi.order_status NOT IN ('canceled', 'unavailable')
      AND d.year_month BETWEEN %(month_from)s AND %(month_to)s
      AND (%(states)s::text[] IS NULL OR COALESCE(dg.state, 'Unknown') = ANY(%(states)s::text[]))
),
cat_orders AS (SELECT DISTINCT order_id FROM cat_items)
SELECT
    (SELECT SUM(price) FROM cat_items)                                         AS revenue,
    COUNT(*)                                                                   AS orders,
    AVG(fo.avg_review_score)                                                   AS review,
    100.0 * COUNT(*) FILTER (WHERE fo.is_late) / NULLIF(COUNT(fo.is_late), 0)  AS late_pct,
    AVG(fo.delivery_days)                                                      AS delivery_days
FROM cat_orders co
JOIN analytics.fact_orders fo ON fo.order_id = co.order_id
"""


@pytest.mark.parametrize("category, month_from, month_to, states", [
    ("health_beauty", "2017-01", "2018-08", None),
    ("bed_bath_table", "2018-01", "2018-06", ["SP"]),
    ("office_furniture", "2016-09", "2018-10", None),
])
def test_full_category_filter_matches_sql(category, month_from, month_to, states, full_db, frames):
    rows = m.apply_filters(frames["categories"], month_from, month_to, None, states)
    demo = m.category_kpis(rows[rows["category"] == category.replace("_", " ")])
    with psycopg.connect(full_db) as conn:
        cur = conn.execute(CATEGORY_SQL, dict(category=category, month_from=month_from, month_to=month_to, states=states))
        sql = {c.name: float(v) for c, v in zip(cur.description, cur.fetchone())}
    assert demo["revenue"] == pytest.approx(sql["revenue"], abs=0.01)
    assert demo["orders"] == sql["orders"]
    for key in ("review", "late_pct", "delivery_days"):
        assert demo[key] == pytest.approx(sql[key], rel=1e-9), key


def test_category_kpis_refuse_multiple_categories(frames):
    with pytest.raises(ValueError):
        m.category_kpis(frames["categories"])
