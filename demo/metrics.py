"""Pure pandas logic behind the demo: loading, filtering and KPI re-aggregation.

Kept free of Streamlit so tests can check every KPI against SQL under any filter.
Definitions mirror reporting.vw_executive_summary:
  revenue / orders / AOV / freight  -> valid orders only (status not canceled/unavailable)
  review score, delivery days, late -> all orders; late rate over delivered orders with valid dates
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"
TABLES = ("orders", "categories", "sellers", "delivery_buckets")
ANALYSIS_WINDOW = ("2017-01", "2018-08")


def load_frames(data_dir: Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    frames = {name: pd.read_parquet(data_dir / f"{name}.parquet") for name in TABLES}
    frames["categories"]["category"] = frames["categories"]["category"].str.replace("_", " ")
    return frames


def load_json(name: str, data_dir: Path = DATA_DIR) -> dict:
    path = data_dir / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else float("nan")


def apply_filters(
    frame: pd.DataFrame,
    month_from: str,
    month_to: str,
    regions: list[str] | None = None,
    states: list[str] | None = None,
) -> pd.DataFrame:
    mask = frame["year_month"].between(month_from, month_to)
    if regions:
        mask &= frame["customer_region"].isin(regions)
    if states:
        mask &= frame["customer_state"].isin(states)
    return frame[mask]


def kpis(orders: pd.DataFrame) -> dict[str, float]:
    valid = orders[orders["is_valid_order"]]
    return {
        "revenue": float(valid["revenue"].sum()),
        "gross_revenue": float(orders["revenue"].sum()),
        "orders": int(valid["orders"].sum()),
        "aov": ratio(valid["revenue"].sum(), valid["orders"].sum()),
        "freight": float(valid["freight"].sum()),
        "freight_pct": 100 * ratio(valid["freight"].sum(), valid["revenue"].sum()),
        "review": ratio(orders["review_sum"].sum(), orders["review_n"].sum()),
        "late_orders": int(orders["late_orders"].sum()),
        "late_pct": 100 * ratio(orders["late_orders"].sum(), orders["valid_delivery_orders"].sum()),
        "delivery_days": ratio(orders["delivery_days_sum"].sum(), orders["delivery_days_n"].sum()),
    }


def category_table(categories: pd.DataFrame) -> pd.DataFrame:
    cat = categories.groupby("category", as_index=False)[["revenue", "items", "orders", "review_sum", "review_n"]].sum()
    cat["share"] = 100 * cat["revenue"] / cat["revenue"].sum() if len(cat) else 0.0
    cat["avg_item_price"] = cat["revenue"] / cat["items"]
    cat["review"] = cat["review_sum"] / cat["review_n"].where(cat["review_n"] > 0)
    return cat.sort_values("revenue", ascending=False).reset_index(drop=True)


def seller_table(sellers: pd.DataFrame) -> pd.DataFrame:
    sel = sellers.groupby(["seller_id", "seller_state"], as_index=False)[
        ["revenue", "orders", "items", "late_orders", "valid_delivery_orders", "review_sum", "review_n"]
    ].sum()
    sel["late_pct"] = 100 * sel["late_orders"] / sel["valid_delivery_orders"].where(sel["valid_delivery_orders"] > 0)
    sel["review"] = sel["review_sum"] / sel["review_n"].where(sel["review_n"] > 0)
    return sel.sort_values("revenue", ascending=False).reset_index(drop=True)


def at_risk_sellers(sel: pd.DataFrame, min_orders: int = 30, max_review: float = 3.8, min_late_pct: float = 10) -> pd.DataFrame:
    sizable = sel[sel["orders"] >= min_orders].copy()
    sizable["at_risk"] = (sizable["review"] < max_review) & (sizable["late_pct"] > min_late_pct)
    return sizable


def brl(value: float, decimals: int = 2) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "–"
    if abs(value) >= 1e6:
        return f"R${value / 1e6:,.{decimals}f}M"
    if abs(value) >= 1e3:
        return f"R${value / 1e3:,.0f}K"
    return f"R${value:,.2f}"
