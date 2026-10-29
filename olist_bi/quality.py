"""Data-quality and reconciliation checks against the built warehouse.

Every check is one SQL query returning a single number (usually a count of
violating rows, or an absolute money difference). A check passes when that
number is <= its tolerance. `error` checks fail the run; `warn` checks are
known, documented source-data characteristics that are reported but tolerated.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import psycopg

NET = "order_status NOT IN ('canceled', 'unavailable')"


@dataclass(frozen=True)
class Check:
    name: str
    category: str
    description: str
    sql: str
    severity: str = "error"
    tolerance: float = 0


@dataclass(frozen=True)
class CheckResult:
    check: Check
    value: float

    @property
    def passed(self) -> bool:
        return self.value <= self.check.tolerance

    @property
    def status(self) -> str:
        if self.passed:
            return "PASS"
        return "FAIL" if self.check.severity == "error" else "WARN"


def _pk_check(table: str, key: str) -> Check:
    return Check(
        name=f"unique_pk_{table.split('.')[1]}",
        category="primary keys",
        description=f"{table} has exactly one row per ({key})",
        sql=f"SELECT COUNT(*) - COUNT(DISTINCT ({key})) FROM {table}",
    )


def _fk_check(child: str, column: str, parent: str, parent_column: str) -> Check:
    return Check(
        name=f"fk_{child.split('.')[1]}_{column}",
        category="foreign keys",
        description=f"every {child}.{column} exists in {parent}",
        sql=(
            f"SELECT COUNT(*) FROM {child} c LEFT JOIN {parent} p ON p.{parent_column} = c.{column} "
            f"WHERE c.{column} IS NOT NULL AND p.{parent_column} IS NULL"
        ),
    )


def _not_null_check(table: str, columns: list[str]) -> Check:
    predicate = " OR ".join(f"{c} IS NULL" for c in columns)
    return Check(
        name=f"not_null_{table.split('.')[1]}",
        category="required fields",
        description=f"{table}: {', '.join(columns)} are never NULL",
        sql=f"SELECT COUNT(*) FROM {table} WHERE {predicate}",
    )


def _money_diff(description: str, name: str, left: str, right: str, tolerance: float = 0.005) -> Check:
    return Check(
        name=name,
        category="reconciliation",
        description=description,
        sql=f"SELECT ABS(({left}) - ({right}))",
        tolerance=tolerance,
    )


NET_REVENUE = f"SELECT SUM(items_revenue) FROM analytics.fact_orders WHERE {NET}"

CHECKS: list[Check] = [
    _pk_check("analytics.dim_date", "date_day"),
    _pk_check("analytics.dim_geography", "zip_code_prefix"),
    _pk_check("analytics.dim_customer", "customer_unique_id"),
    _pk_check("analytics.dim_seller", "seller_id"),
    _pk_check("analytics.dim_product", "product_id"),
    _pk_check("analytics.fact_orders", "order_id"),
    _pk_check("analytics.fact_order_items", "order_id, order_item_id"),
    _pk_check("analytics.fact_payments", "order_id, payment_sequential"),

    _fk_check("analytics.fact_orders", "customer_unique_id", "analytics.dim_customer", "customer_unique_id"),
    _fk_check("analytics.fact_orders", "order_date_key", "analytics.dim_date", "date_day"),
    _fk_check("analytics.fact_order_items", "product_id", "analytics.dim_product", "product_id"),
    _fk_check("analytics.fact_order_items", "seller_id", "analytics.dim_seller", "seller_id"),
    _fk_check("analytics.fact_order_items", "order_id", "analytics.fact_orders", "order_id"),
    _fk_check("analytics.fact_payments", "order_id", "analytics.fact_orders", "order_id"),
    Check(
        name="customer_zip_in_geography",
        category="foreign keys",
        description="customers whose ZIP prefix is absent from the public geolocation file "
                    "(source-data gap; kept in an explicit 'Unknown' bucket, never dropped)",
        sql="SELECT COUNT(*) FROM analytics.dim_customer c "
            "LEFT JOIN analytics.dim_geography g USING (zip_code_prefix) WHERE g.zip_code_prefix IS NULL",
        severity="warn",
    ),

    _not_null_check("analytics.fact_orders", ["order_id", "customer_unique_id", "order_date_key", "order_status"]),
    _not_null_check("analytics.fact_order_items", ["order_id", "product_id", "seller_id", "price", "order_date_key"]),
    _not_null_check("analytics.fact_payments", ["order_id", "payment_type", "payment_value"]),
    _not_null_check("analytics.dim_product", ["category_name_en"]),
    _not_null_check("analytics.dim_customer", ["zip_code_prefix", "state"]),

    Check(
        name="row_count_orders",
        category="completeness",
        description="fact_orders keeps every raw order (no rows lost or duplicated by joins)",
        sql="SELECT ABS((SELECT COUNT(*) FROM raw.orders) - (SELECT COUNT(*) FROM analytics.fact_orders))",
    ),
    Check(
        name="row_count_order_items",
        category="completeness",
        description="fact_order_items keeps every raw order item",
        sql="SELECT ABS((SELECT COUNT(*) FROM raw.order_items) - (SELECT COUNT(*) FROM analytics.fact_order_items))",
    ),
    Check(
        name="row_count_payments",
        category="completeness",
        description="fact_payments keeps every raw payment",
        sql="SELECT ABS((SELECT COUNT(*) FROM raw.order_payments) - (SELECT COUNT(*) FROM analytics.fact_payments))",
    ),
    Check(
        name="customers_complete",
        category="completeness",
        description="dim_customer has one row per distinct raw customer_unique_id",
        sql="SELECT ABS((SELECT COUNT(DISTINCT customer_unique_id) FROM raw.customers) "
            "- (SELECT COUNT(*) FROM analytics.dim_customer))",
    ),

    Check(
        name="no_negative_money",
        category="monetary values",
        description="no negative price, freight or payment value",
        sql="SELECT (SELECT COUNT(*) FROM analytics.fact_order_items WHERE price < 0 OR freight_value < 0) "
            "+ (SELECT COUNT(*) FROM analytics.fact_payments WHERE payment_value < 0)",
    ),
    Check(
        name="zero_price_items",
        category="monetary values",
        description="order items with a zero price",
        sql="SELECT COUNT(*) FROM analytics.fact_order_items WHERE price = 0",
    ),
    Check(
        name="zero_value_payments",
        category="monetary values",
        description="payment rows with value 0 (vouchers / not_defined in the source data)",
        sql="SELECT COUNT(*) FROM analytics.fact_payments WHERE payment_value = 0",
        severity="warn",
    ),
    Check(
        name="valid_orders_without_items",
        category="monetary values",
        description="valid (non-canceled) orders with no item rows -- counted as orders, R$0 revenue",
        sql=f"SELECT COUNT(*) FROM analytics.fact_orders WHERE {NET} AND n_items = 0",
        severity="warn",
    ),

    Check(
        name="no_negative_delivery_days",
        category="dates",
        description="delivery_days is never negative (impossible date orderings are NULLed in staging)",
        sql="SELECT COUNT(*) FROM analytics.fact_orders WHERE delivery_days < 0",
    ),
    Check(
        name="delivered_before_purchase",
        category="dates",
        description="no customer delivery date earlier than the purchase timestamp",
        sql="SELECT COUNT(*) FROM raw.orders WHERE order_delivered_customer_date < order_purchase_timestamp",
    ),
    Check(
        name="delivered_before_carrier",
        category="dates",
        description="orders delivered to the customer before carrier handoff (source error; excluded from delivery KPIs)",
        sql="SELECT COUNT(*) FROM raw.orders WHERE order_delivered_customer_date < order_delivered_carrier_date",
        severity="warn",
    ),
    Check(
        name="order_dates_in_dim_date",
        category="dates",
        description="every order date falls inside dim_date",
        sql="SELECT COUNT(*) FROM analytics.fact_orders f LEFT JOIN analytics.dim_date d "
            "ON d.date_day = f.order_date_key WHERE d.date_day IS NULL",
    ),
    Check(
        name="late_flag_only_for_delivered",
        category="dates",
        description="is_late is only populated for delivered orders with valid dates",
        sql="SELECT COUNT(*) FROM analytics.fact_orders WHERE is_late IS NOT NULL "
            "AND NOT (is_delivered AND has_valid_delivery_dates)",
    ),

    Check(
        name="late_flag_uses_calendar_dates",
        category="dates",
        description="is_late == (delivered calendar date > promised calendar date) for every measurable delivery",
        sql="SELECT COUNT(*) FROM analytics.fact_orders f JOIN raw.orders o USING (order_id) "
            "WHERE f.is_late IS NOT NULL AND f.is_late <> "
            "(o.order_delivered_customer_date::date > o.order_estimated_delivery_date::date)",
    ),
    Check(
        name="promised_date_is_calendar_date",
        category="dates",
        description="estimated delivery dates carry no time of day (justifies the calendar-date late rule)",
        sql="SELECT COUNT(*) FROM raw.orders WHERE order_estimated_delivery_date::time <> TIME '00:00'",
    ),

    _money_diff(
        "gross revenue: fact_orders (order grain) == raw.order_items (no fan-out)",
        "no_fanout_gross_revenue",
        "SELECT SUM(items_revenue) FROM analytics.fact_orders",
        "SELECT SUM(price) FROM raw.order_items",
    ),
    _money_diff(
        "gross freight: fact_orders == raw.order_items",
        "no_fanout_freight",
        "SELECT SUM(freight_total) FROM analytics.fact_orders",
        "SELECT SUM(freight_value) FROM raw.order_items",
    ),
    _money_diff(
        "payments: fact_orders.payments_total == raw.order_payments",
        "no_fanout_payments",
        "SELECT SUM(payments_total) FROM analytics.fact_orders",
        "SELECT SUM(payment_value) FROM raw.order_payments",
    ),
    _money_diff(
        "net revenue: order grain (fact_orders) == item grain (fact_order_items)",
        "net_revenue_order_vs_item_grain",
        NET_REVENUE,
        f"SELECT SUM(price) FROM analytics.fact_order_items WHERE {NET}",
    ),
    _money_diff(
        "net revenue == SUM(reporting.vw_category_performance.revenue)",
        "category_view_reconciles",
        NET_REVENUE,
        "SELECT SUM(revenue) FROM reporting.vw_category_performance",
        tolerance=0.5,  # per-category ROUND(…, 2)
    ),
    _money_diff(
        "net revenue == SUM(reporting.vw_seller_performance.revenue)",
        "seller_view_reconciles",
        NET_REVENUE,
        "SELECT SUM(revenue) FROM reporting.vw_seller_performance",
        tolerance=0.5,
    ),
    _money_diff(
        "net revenue == SUM(reporting.vw_customer_geography_performance.revenue)",
        "geography_view_reconciles",
        NET_REVENUE,
        "SELECT SUM(revenue) FROM reporting.vw_customer_geography_performance",
        tolerance=0.5,
    ),
    _money_diff(
        "net revenue == reporting.vw_executive_summary.net_revenue",
        "executive_view_reconciles",
        NET_REVENUE,
        "SELECT net_revenue FROM reporting.vw_executive_summary",
    ),
    Check(
        name="payments_vs_items_plus_freight",
        category="reconciliation",
        description="abs(payments - (items + freight)) on valid orders, as % of payments "
                    "(vouchers/installment interest make small gaps expected)",
        sql=f"SELECT 100 * ABS(SUM(payments_total) - SUM(items_revenue + freight_total)) / SUM(payments_total) "
            f"FROM analytics.fact_orders WHERE {NET} AND payments_total IS NOT NULL",
        severity="warn",
        tolerance=0.1,
    ),
]


def run_checks(database_url: str, checks: list[Check] | None = None) -> list[CheckResult]:
    results = []
    with psycopg.connect(database_url) as conn:
        for check in checks or CHECKS:
            value = conn.execute(check.sql).fetchone()[0]
            value = float(value) if isinstance(value, Decimal) else (value or 0)
            results.append(CheckResult(check, float(value)))
    return results


def format_report(results: list[CheckResult]) -> str:
    lines = [
        "| Status | Category | Check | Value | Tolerance |",
        "|---|---|---|---:|---:|",
    ]
    for r in results:
        value = f"{r.value:,.4f}".rstrip("0").rstrip(".") if r.value % 1 else f"{int(r.value):,}"
        lines.append(f"| {r.status} | {r.check.category} | {r.check.description} | {value} | {r.check.tolerance:g} |")
    failed = sum(r.status == "FAIL" for r in results)
    warned = sum(r.status == "WARN" for r in results)
    passed = sum(r.passed for r in results)
    lines.append("")
    lines.append(f"**{passed} passed, {warned} warnings, {failed} failed** (of {len(results)} checks)")
    return "\n".join(lines)
