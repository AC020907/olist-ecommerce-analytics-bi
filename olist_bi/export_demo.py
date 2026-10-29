"""Export small, additive pre-aggregates from the warehouse for the Streamlit demo.

The demo never recomputes business rules: every table below is a GROUP BY over
the analytics star schema using the same filters as the reporting views
(valid orders = status not canceled/unavailable). Everything exported is a sum or
a count, so the app can re-aggregate after any date/state filter and still
reproduce the SQL KPIs exactly (averages are rebuilt as sum / count).
"""
from __future__ import annotations

import json
import logging
from datetime import date
from decimal import Decimal
from pathlib import Path

import pandas as pd
import psycopg

from .config import REPO_ROOT
from .quality import run_checks

log = logging.getLogger(__name__)

DEMO_DATA_DIR = REPO_ROOT / "demo" / "data"

# Same customer geography as reporting.vw_customer_geography_performance and the Power BI
# model (dim_customer.zip_code_prefix -> dim_geography); ZIPs missing from the public
# geolocation file stay in an explicit 'Unknown' bucket so totals still reconcile.
_CUSTOMER_GEO = """
customer_geo AS (
    SELECT dc.customer_unique_id,
           COALESCE(dg.state, 'Unknown')  AS customer_state,
           COALESCE(dg.region, 'Unknown') AS customer_region
    FROM analytics.dim_customer dc
    LEFT JOIN analytics.dim_geography dg ON dg.zip_code_prefix = dc.zip_code_prefix
)"""

_DELAY_BUCKET = """CASE
        WHEN NOT is_late      THEN '0. On time or early'
        WHEN days_late = 1    THEN '1. 1 day late'
        WHEN days_late <= 3   THEN '2. 2-3 days late'
        WHEN days_late <= 7   THEN '3. 4-7 days late'
        WHEN days_late <= 14  THEN '4. 8-14 days late'
        ELSE                       '5. 15+ days late'
    END"""

QUERIES: dict[str, str] = {
    # Order grain. Keeps canceled/unavailable rows (is_valid_order = false) because the
    # project's delivery and review KPIs are computed over all orders, while revenue and
    # order counts use valid orders only -- see reporting.vw_executive_summary.
    "orders": f"""
WITH {_CUSTOMER_GEO}
SELECT
    d.year_month,
    g.customer_state,
    g.customer_region,
    fo.order_status NOT IN ('canceled', 'unavailable')                 AS is_valid_order,
    COUNT(*)                                                             AS orders,
    SUM(fo.items_revenue)                                                AS revenue,
    SUM(fo.freight_total)                                                AS freight,
    SUM(fo.n_items)                                                      AS items,
    SUM(fo.delivery_days)                                                AS delivery_days_sum,
    COUNT(fo.delivery_days)                                              AS delivery_days_n,
    COUNT(*) FILTER (WHERE fo.is_late)                                   AS late_orders,
    COUNT(*) FILTER (WHERE fo.is_late IS NOT NULL)                  AS valid_delivery_orders,
    SUM(fo.avg_review_score)                                             AS review_sum,
    COUNT(fo.avg_review_score)                                           AS review_n
FROM analytics.fact_orders fo
JOIN analytics.dim_date d ON d.date_day = fo.order_date_key
JOIN customer_geo g ON g.customer_unique_id = fo.customer_unique_id
GROUP BY 1, 2, 3, 4
""",
    # Item grain, valid orders only (same population as vw_category_performance).
    # Review score is averaged over distinct (category, order) pairs, never per item.
    "categories": f"""
WITH {_CUSTOMER_GEO},
items AS (
    SELECT foi.order_id, foi.price, dp.category_name_en AS category, d.year_month, g.customer_state, g.customer_region
    FROM analytics.fact_order_items foi
    JOIN analytics.dim_product dp ON dp.product_id = foi.product_id
    JOIN analytics.dim_date d ON d.date_day = foi.order_date_key
    JOIN customer_geo g ON g.customer_unique_id = foi.customer_unique_id
    WHERE foi.order_status NOT IN ('canceled', 'unavailable')
),
item_totals AS (
    SELECT year_month, customer_state, customer_region, category,
           COUNT(*) AS items, COUNT(DISTINCT order_id) AS orders, SUM(price) AS revenue
    FROM items GROUP BY 1, 2, 3, 4
),
order_outcomes AS (
    -- Order-level outcomes for the distinct orders that contain the category, so a
    -- single-category filter can drive orders / late rate / reviews without fan-out.
    SELECT i.year_month, i.customer_state, i.customer_region, i.category,
           SUM(fo.avg_review_score) AS review_sum, COUNT(fo.avg_review_score) AS review_n,
           SUM(fo.delivery_days) AS delivery_days_sum, COUNT(fo.delivery_days) AS delivery_days_n,
           COUNT(*) FILTER (WHERE fo.is_late) AS late_orders,
           COUNT(*) FILTER (WHERE fo.is_late IS NOT NULL) AS valid_delivery_orders
    FROM (SELECT DISTINCT year_month, customer_state, customer_region, category, order_id FROM items) i
    JOIN analytics.fact_orders fo ON fo.order_id = i.order_id
    GROUP BY 1, 2, 3, 4
)
SELECT t.*, o.review_sum, o.review_n, o.delivery_days_sum, o.delivery_days_n, o.late_orders, o.valid_delivery_orders
FROM item_totals t
JOIN order_outcomes o USING (year_month, customer_state, customer_region, category)
""",
    # Delay buckets for the distinct valid orders containing each category (single-category filter).
    "category_delivery_buckets": f"""
WITH {_CUSTOMER_GEO},
category_orders AS (
    SELECT DISTINCT dp.category_name_en AS category, foi.order_id
    FROM analytics.fact_order_items foi
    JOIN analytics.dim_product dp ON dp.product_id = foi.product_id
    WHERE foi.order_status NOT IN ('canceled', 'unavailable')
),
delivered AS (
    SELECT co.category, fo.is_late, fo.avg_review_score, d.year_month, g.customer_state, g.customer_region,
           o.order_delivered_customer_date::date - o.order_estimated_delivery_date::date AS days_late
    FROM category_orders co
    JOIN analytics.fact_orders fo ON fo.order_id = co.order_id
    JOIN raw.orders o ON o.order_id = fo.order_id
    JOIN analytics.dim_date d ON d.date_day = fo.order_date_key
    JOIN customer_geo g ON g.customer_unique_id = fo.customer_unique_id
    WHERE fo.is_late IS NOT NULL
)
SELECT
    year_month, customer_state, customer_region, category,
    {_DELAY_BUCKET} AS delay_bucket,
    COUNT(*) AS orders,
    SUM(avg_review_score) AS review_sum,
    COUNT(avg_review_score) AS review_n,
    COUNT(*) FILTER (WHERE avg_review_score <= 2) AS low_review_orders
FROM delivered
GROUP BY 1, 2, 3, 4, 5
""",
    # Seller x month x customer state, valid orders only (same population as vw_seller_performance).
    "sellers": f"""
WITH {_CUSTOMER_GEO},
items AS (
    SELECT foi.seller_id, ds.state AS seller_state, foi.order_id, foi.price,
           d.year_month, g.customer_state, g.customer_region
    FROM analytics.fact_order_items foi
    JOIN analytics.dim_seller ds ON ds.seller_id = foi.seller_id
    JOIN analytics.dim_date d ON d.date_day = foi.order_date_key
    JOIN customer_geo g ON g.customer_unique_id = foi.customer_unique_id
    WHERE foi.order_status NOT IN ('canceled', 'unavailable')
),
item_totals AS (
    SELECT seller_id, seller_state, year_month, customer_state, customer_region,
           COUNT(*) AS items, COUNT(DISTINCT order_id) AS orders, SUM(price) AS revenue
    FROM items GROUP BY 1, 2, 3, 4, 5
),
order_outcomes AS (
    SELECT s.seller_id, s.year_month, s.customer_state,
           SUM(fo.delivery_days) AS delivery_days_sum, COUNT(fo.delivery_days) AS delivery_days_n,
           COUNT(*) FILTER (WHERE fo.is_late) AS late_orders,
           COUNT(*) FILTER (WHERE fo.is_late IS NOT NULL) AS valid_delivery_orders,
           SUM(fo.avg_review_score) AS review_sum, COUNT(fo.avg_review_score) AS review_n
    FROM (SELECT DISTINCT seller_id, year_month, customer_state, order_id FROM items) s
    JOIN analytics.fact_orders fo ON fo.order_id = s.order_id
    GROUP BY 1, 2, 3
)
SELECT t.*, o.delivery_days_sum, o.delivery_days_n, o.late_orders, o.valid_delivery_orders, o.review_sum, o.review_n
FROM item_totals t
JOIN order_outcomes o USING (seller_id, year_month, customer_state)
""",
    # Delivered orders with valid dates, bucketed by calendar days past the promised date
    # (same rule as is_late: a delivery on the promised day is on time).
    "delivery_buckets": f"""
WITH {_CUSTOMER_GEO},
delivered AS (
    SELECT fo.order_id, fo.is_late, fo.avg_review_score, d.year_month, g.customer_state, g.customer_region,
           o.order_delivered_customer_date::date - o.order_estimated_delivery_date::date AS days_late
    FROM analytics.fact_orders fo
    JOIN raw.orders o ON o.order_id = fo.order_id
    JOIN analytics.dim_date d ON d.date_day = fo.order_date_key
    JOIN customer_geo g ON g.customer_unique_id = fo.customer_unique_id
    WHERE fo.is_late IS NOT NULL
)
SELECT
    year_month, customer_state, customer_region,
    {_DELAY_BUCKET} AS delay_bucket,
    COUNT(*) AS orders,
    SUM(avg_review_score) AS review_sum,
    COUNT(avg_review_score) AS review_n,
    COUNT(*) FILTER (WHERE avg_review_score <= 2) AS low_review_orders
FROM delivered
GROUP BY 1, 2, 3, 4
""",
}

REFERENCE_SQL = "SELECT * FROM reporting.vw_executive_summary"
PERIOD_SQL = "SELECT MIN(order_purchase_timestamp)::date, MAX(order_purchase_timestamp)::date FROM raw.orders"


def _to_frame(cur: psycopg.Cursor) -> pd.DataFrame:
    columns = [c.name for c in cur.description]
    frame = pd.DataFrame(cur.fetchall(), columns=columns)
    for column in frame.columns:
        if frame[column].map(lambda v: isinstance(v, Decimal)).any():
            frame[column] = frame[column].astype(float)  # NUMERIC -> float for parquet/plotly
    return frame


def export(database_url: str, out_dir: Path = DEMO_DATA_DIR) -> dict[str, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    sizes: dict[str, int] = {}
    with psycopg.connect(database_url) as conn, conn.cursor() as cur:
        for name, sql in QUERIES.items():
            cur.execute(sql)
            frame = _to_frame(cur)
            # Stable row order keeps re-exports byte-comparable in git diffs.
            frame = frame.sort_values(list(frame.columns[:5])).reset_index(drop=True)
            frame.to_parquet(out_dir / f"{name}.parquet", index=False)
            sizes[name] = len(frame)
            log.info("  %-18s %7d rows", name, len(frame))
        cur.execute(REFERENCE_SQL)
        reference = {k: float(v) for k, v in zip([c.name for c in cur.description], cur.fetchone())}
        cur.execute(PERIOD_SQL)
        first_order, last_order = cur.fetchone()
    (out_dir / "kpi_reference.json").write_text(json.dumps(reference, indent=2), encoding="utf-8")
    metadata = {
        "first_order_date": first_order.isoformat(),
        "last_order_date": last_order.isoformat(),
        "exported_on": date.today().isoformat(),
        "source": "Olist Brazilian E-Commerce Public Dataset (Kaggle, CC BY-NC-SA 4.0)",
    }
    (out_dir / "export_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    quality = [
        {"check": r.check.name, "category": r.check.category, "description": r.check.description,
         "severity": r.check.severity, "value": r.value, "tolerance": r.check.tolerance, "status": r.status}
        for r in run_checks(database_url)
    ]
    (out_dir / "quality_summary.json").write_text(json.dumps(quality, indent=2), encoding="utf-8")
    return sizes
