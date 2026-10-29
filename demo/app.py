"""Olist Sales Analytics -- public Streamlit app built on the Olist BI warehouse.

Reads only the pre-aggregates in demo/data/ (written by `python -m olist_bi export`),
so it needs no database. KPI logic lives in metrics.py and mirrors the SQL views:
revenue / orders / AOV use valid orders (not canceled/unavailable); review score uses
all reviewed orders; late rate = delivered on a later calendar day than promised,
over delivered orders with valid dates. With a category selected, KPIs describe the
valid orders that contain that category.

Run:  streamlit run demo/app.py
"""
from __future__ import annotations

import importlib
import logging
import time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import metrics

# Streamlit Community Cloud pulls new commits without restarting the Python process, so
# a metrics module imported by the previous version would stay in memory and break the
# new app.py. Reloading it on every script run is cheap and keeps both files in sync.
m = importlib.reload(metrics)

BLUE = "#2a78d6"
ORANGE = "#eb6834"
MUTED = "#a3a29c"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e8e7e3"
MIN_SELLER_ORDERS = 30
ALL_CATEGORIES = "All categories"
REPO_URL = "https://github.com/AC020907/olist-ecommerce-analytics-bi"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("olist_app")

st.set_page_config(
    page_title="Olist Sales Analytics · BI portfolio",
    page_icon=":bar_chart:",
    layout="wide",
    menu_items={"About": f"Independent portfolio project on public Olist data. Code: {REPO_URL}"},
)

st.markdown(
    """
<style>
.block-container {padding-top: 3.2rem; max-width: 1280px;}
[data-testid="stMetric"] {background: #ffffff; border: 1px solid #e8e7e3; border-radius: 10px; padding: 14px 16px;}
[data-testid="stMetricLabel"] p {color: #52514e; font-size: 0.85rem;}
[data-testid="stMetricValue"] {font-size: 1.6rem;}
.eyebrow {color: #2a78d6; font-weight: 600; letter-spacing: .04em; text-transform: uppercase; font-size: .78rem; margin-bottom: .2rem;}
.lede {color: #52514e; font-size: 1.02rem; max-width: 820px;}
.note {color: #52514e; font-size: .85rem;}
.chips {margin: .2rem 0 .8rem 0;}
.chip {display: inline-block; background: #eef4fc; color: #1d5fae; border-radius: 999px; padding: 2px 10px; margin: 0 6px 6px 0; font-size: .8rem;}
.card {background: #ffffff; border: 1px solid #e8e7e3; border-left: 4px solid #2a78d6; border-radius: 8px; padding: 14px 16px; margin-bottom: 12px;}
.card h4 {margin: 0 0 6px 0; font-size: 1rem;}
.card p {margin: 0 0 4px 0; color: #303030; font-size: .93rem;}
.card .label {color: #52514e; font-weight: 600;}
@media (max-width: 640px) {
  .block-container {padding-left: 1rem; padding-right: 1rem; padding-top: 3.5rem;}
  h1 {font-size: 1.7rem !important;}
}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Loading data…")
def load() -> tuple[dict[str, pd.DataFrame], dict, dict, list]:
    started = time.perf_counter()
    frames = m.load_frames()
    reference = m.load_json("kpi_reference.json")
    metadata = m.load_json("export_metadata.json")
    quality = m.load_json("quality_summary.json") or []
    log.info("data loaded in %.2fs: %s", time.perf_counter() - started, {k: len(v) for k, v in frames.items()})
    return frames, reference, metadata, quality


def style(fig: go.Figure, height: int = 340, **layout) -> go.Figure:
    defaults = dict(
        height=height,
        margin=dict(l=8, r=8, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=INK_2, size=12),
        hoverlabel=dict(bgcolor="#ffffff", font_color=INK, bordercolor=GRID),
        showlegend=False,
        barcornerradius=4,
        bargap=0.25,
    )
    fig.update_layout(**{**defaults, **layout})
    fig.update_xaxes(showgrid=False, linecolor=GRID, tickfont_color=INK_2)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, tickfont_color=INK_2)
    return fig


def show(fig: go.Figure) -> None:
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def fmt_num(value: float, pattern: str) -> str:
    return "–" if value is None or pd.isna(value) else pattern.format(value)


def card(title: str, rows: list[tuple[str, str]]) -> None:
    body = "".join(f"<p><span class='label'>{label}:</span> {text}</p>" for label, text in rows)
    st.markdown(f"<div class='card'><h4>{title}</h4>{body}</div>", unsafe_allow_html=True)


try:
    data, reference, metadata, quality = load()
except Exception:  # missing/corrupt export: show a clear message instead of a stack trace
    log.exception("failed to load demo data")
    st.error("The dashboard data could not be loaded. Please try again later.")
    st.stop()

months = sorted(data["orders"]["year_month"].unique())
regions = sorted(data["orders"]["customer_region"].unique())
categories_all = sorted(data["categories"]["category"].unique())

# ---------------------------------------------------------------- filters

FILTER_KEYS = ("period", "regions", "states", "category")


def reset_filters() -> None:
    # Dropping the widget state makes every filter fall back to its declared default.
    for key in FILTER_KEYS:
        st.session_state.pop(key, None)


with st.sidebar:
    st.markdown("### Filters")
    start, end = st.select_slider(
        "Order month", options=months, value=m.ANALYSIS_WINDOW, key="period",
        help="Default is Jan 2017 – Aug 2018, the window with complete monthly data. "
             "Sep–Dec 2016 and Sep–Oct 2018 are partial edges of the public dataset.",
    )
    region_sel = st.multiselect("Customer region", regions, key="regions", placeholder="All regions",
                                help="'Unknown' = customers whose ZIP prefix is missing from the public geolocation file.")
    state_options = sorted(
        data["orders"].loc[data["orders"]["customer_region"].isin(region_sel or regions), "customer_state"].unique()
    )
    if "states" in st.session_state:  # drop states that the region selection no longer offers
        st.session_state["states"] = [s for s in st.session_state["states"] if s in state_options]
    state_sel = st.multiselect("Customer state", state_options, key="states", placeholder="All states")
    category_sel = st.selectbox(
        "Product category", [ALL_CATEGORIES] + categories_all, key="category",
        help="One category at a time: KPIs then describe valid orders that contain it. "
             "Several categories cannot be combined without counting multi-category orders twice.",
    )
    st.button("Reset filters", on_click=reset_filters, width="stretch")
    st.divider()
    period = f"{metadata.get('first_order_date', '2016-09-04')} to {metadata.get('last_order_date', '2018-10-17')}"
    exported = metadata.get("exported_on")
    st.markdown(
        f"<p class='note'><b>Historical snapshot, not live data.</b> Orders from {period}, "
        "Brazilian E-Commerce Public Dataset by Olist (Kaggle, CC BY-NC-SA 4.0)."
        + (f" Aggregates generated from the warehouse on {exported}." if exported else "")
        + f" Independent portfolio project, not affiliated with Olist. <a href='{REPO_URL}'>Source code</a>.</p>",
        unsafe_allow_html=True,
    )

if start not in months or end not in months or start > end:  # defensive: widget values come from session state
    log.warning("invalid period %s-%s, resetting", start, end)
    start, end = m.ANALYSIS_WINDOW
category_mode = category_sel != ALL_CATEGORIES
log.info("filters period=%s..%s regions=%s states=%s category=%s", start, end, region_sel, state_sel, category_sel)


def apply_filters(frame: pd.DataFrame, month_from: str | None = None, month_to: str | None = None) -> pd.DataFrame:
    return m.apply_filters(frame, month_from or start, month_to or end, region_sel, state_sel)


def for_category(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[frame["category"] == category_sel]


orders = apply_filters(data["orders"])
categories = apply_filters(data["categories"])
sellers = apply_filters(data["sellers"])
if category_mode:
    cat_rows = for_category(categories)
    buckets = for_category(apply_filters(data["category_delivery_buckets"]))
    current = m.category_kpis(cat_rows)
else:
    cat_rows = categories
    buckets = apply_filters(data["delivery_buckets"])
    current = m.kpis(orders)

# Comparison period of equal length immediately before the selection, only when it
# stays inside the complete-data window (otherwise growth vs. a partial month is noise).
span = months.index(end) - months.index(start) + 1
prev_start_idx = months.index(start) - span
previous = None
if prev_start_idx >= 0 and months[prev_start_idx] >= m.ANALYSIS_WINDOW[0]:
    prev_from, prev_to = months[prev_start_idx], months[months.index(start) - 1]
    if category_mode:
        prev_rows = for_category(apply_filters(data["categories"], prev_from, prev_to))
        previous = m.category_kpis(prev_rows) if len(prev_rows) else None
    else:
        previous = m.kpis(apply_filters(data["orders"], prev_from, prev_to))


def delta(key: str, fmt: str = "{:+.1f}%", relative: bool = True) -> str | None:
    if previous is None or pd.isna(previous.get(key)) or not previous.get(key) or pd.isna(current[key]):
        return None
    change = (current[key] / previous[key] - 1) * 100 if relative else current[key] - previous[key]
    return fmt.format(change)


# ---------------------------------------------------------------- header

st.markdown("<div class='eyebrow'>Sales Analytics &amp; Business Intelligence · Interactive dashboard</div>", unsafe_allow_html=True)
st.title("Olist marketplace: sales, delivery and customer satisfaction")
st.markdown(
    "<p class='lede'>A working BI application on 1.5M rows of public Brazilian e-commerce data (2016–2018): "
    "validated revenue, sales drivers, delivery performance and how it relates to reviews. Every number "
    "comes from one tested data model shared with SQL and Power BI.</p>",
    unsafe_allow_html=True,
)
chips = [f"{start} → {end}"]
chips += [f"Region: {', '.join(region_sel)}"] if region_sel else []
chips += [f"State: {', '.join(state_sel)}"] if state_sel else []
chips += [f"Category: {category_sel}"] if category_mode else []
st.markdown("<div class='chips'>" + "".join(f"<span class='chip'>{c}</span>" for c in chips) + "</div>", unsafe_allow_html=True)

if current["orders"] == 0:
    st.warning("No valid orders match these filters. Widen the month range, change the category or press **Reset filters**.")
    st.stop()

overview, sales, delivery, insights, method = st.tabs(
    ["Executive overview", "Sales performance", "Delivery & satisfaction", "Business insights", "Methodology & data quality"]
)

# Series shared by several tabs
if category_mode:
    monthly = cat_rows.groupby("year_month", as_index=False)[["revenue", "orders"]].sum()
    late_src = cat_rows
    state_src = cat_rows.assign(is_valid_order=True)
else:
    monthly = orders[orders["is_valid_order"]].groupby("year_month", as_index=False)[["revenue", "orders"]].sum()
    late_src = orders
    state_src = orders
monthly["aov"] = monthly["revenue"] / monthly["orders"].where(monthly["orders"] > 0)
monthly["mom_pct"] = 100 * monthly["revenue"].pct_change()
late_month = late_src.groupby("year_month", as_index=False)[["late_orders", "valid_delivery_orders"]].sum()
late_month = late_month[late_month["valid_delivery_orders"] > 0]
late_month["late_pct"] = 100 * late_month["late_orders"] / late_month["valid_delivery_orders"]
cat = m.category_table(categories)
sel = m.seller_table(sellers)
sel["seller"] = "Seller " + sel["seller_id"].str[:8]
sizable = m.at_risk_sellers(sel, MIN_SELLER_ORDERS)
at_risk = sizable[sizable["at_risk"]].sort_values("revenue", ascending=False)
on_time = buckets[buckets["delay_bucket"].str.startswith("0.")]
late = buckets[~buckets["delay_bucket"].str.startswith("0.")]
on_time_review = m.ratio(on_time["review_sum"].sum(), on_time["review_n"].sum())
late_review = m.ratio(late["review_sum"].sum(), late["review_n"].sum())
scope = f"orders containing {category_sel}" if category_mode else "all valid orders"

# ---------------------------------------------------------------- executive overview

with overview:
    if previous is None:
        st.caption(f"KPIs for {scope}. Growth deltas appear when an equal-length prior period inside Jan 2017 – Aug 2018 exists.")
    else:
        st.caption(f"KPIs for {scope}. Deltas compare with the previous {span} month(s).")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Net revenue", m.brl(current["revenue"]), delta("revenue"),
              help="Item prices (BRL) on orders not canceled or unavailable; freight excluded. "
                   "With a category selected: that category's items only.")
    c2.metric("Orders", f"{current['orders']:,.0f}", delta("orders"))
    c3.metric("Average order value", m.brl(current["aov"]), delta("aov"))
    c4.metric("Customer satisfaction", fmt_num(current["review"], "{:.2f} / 5"), delta("review", "{:+.2f}", relative=False),
              help="Average review score (1–5); orders with several reviews are averaged first.")
    c5.metric("Late deliveries", fmt_num(current["late_pct"], "{:.1f}%"), delta("late_pct", "{:+.1f} pp", relative=False),
              delta_color="inverse",
              help="Delivered on a later calendar day than promised, among delivered orders with valid dates.")

    left, right = st.columns([2, 1])
    with left:
        st.markdown("##### Monthly net revenue (BRL)")
        fig = go.Figure(go.Bar(
            x=monthly["year_month"], y=monthly["revenue"], marker_color=BLUE,
            customdata=monthly[["orders", "aov"]],
            hovertemplate="<b>%{x}</b><br>Revenue R$%{y:,.0f}<br>Orders %{customdata[0]:,}<br>AOV R$%{customdata[1]:,.2f}<extra></extra>",
        ))
        show(style(fig, yaxis_tickprefix="R$", yaxis_tickformat="~s"))
    with right:
        st.markdown("##### Key highlights")
        best = monthly.loc[monthly["revenue"].idxmax()] if len(monthly) else None
        highlights = []
        if best is not None:
            highlights.append(f"Best month: **{best['year_month']}** with {m.brl(best['revenue'])}.")
        if delta("revenue"):
            highlights.append(f"Revenue **{delta('revenue')}** vs the previous {span} month(s).")
        if not category_mode and len(cat):
            highlights.append(f"Top category: **{cat.iloc[0]['category']}** ({cat.iloc[0]['share']:.1f}% of revenue).")
        if not pd.isna(on_time_review) and not pd.isna(late_review):
            highlights.append(f"On-time orders rate **{on_time_review:.2f}/5**, late ones **{late_review:.2f}/5**.")
        highlights.append(f"Late deliveries: **{fmt_num(current['late_pct'], '{:.1f}%')}** of delivered orders.")
        st.markdown("\n".join(f"- {h}" for h in highlights))

    left, right = st.columns(2)
    with left:
        st.markdown("##### Average order value trend (BRL)")
        fig = go.Figure(go.Scatter(
            x=monthly["year_month"], y=monthly["aov"], mode="lines+markers",
            line=dict(color=BLUE, width=2), marker=dict(size=7),
            hovertemplate="<b>%{x}</b><br>AOV R$%{y:,.2f}<extra></extra>",
        ))
        show(style(fig, height=300, yaxis_tickprefix="R$"))
    with right:
        st.markdown("##### Late-delivery rate trend")
        fig = go.Figure(go.Scatter(
            x=late_month["year_month"], y=late_month["late_pct"], mode="lines+markers",
            line=dict(color=ORANGE, width=2), marker=dict(size=7),
            hovertemplate="<b>%{x}</b><br>Late %{y:.1f}%<extra></extra>",
        ))
        show(style(fig, height=300, yaxis_ticksuffix="%", yaxis_rangemode="tozero"))

# ---------------------------------------------------------------- sales performance

with sales:
    left, right = st.columns(2)
    with left:
        st.markdown("##### Month-over-month revenue growth")
        growth = monthly.dropna(subset=["mom_pct"])
        if growth.empty:
            st.info("Select at least two months to see growth.")
        else:
            fig = go.Figure(go.Bar(
                x=growth["year_month"], y=growth["mom_pct"],
                marker_color=[BLUE if v >= 0 else ORANGE for v in growth["mom_pct"]],
                hovertemplate="<b>%{x}</b><br>%{y:+.1f}% vs previous month<extra></extra>",
            ))
            show(style(fig, height=300, yaxis_ticksuffix="%"))
            st.caption("Blue: growth. Orange: decline. Partial edge months (2016, Sep–Oct 2018) distort growth.")
    with right:
        st.markdown(f"##### Net revenue by customer state (top 10){' — ' + category_sel if category_mode else ''}")
        by_state = state_src[state_src["is_valid_order"]].groupby("customer_state", as_index=False)["revenue"].sum()
        by_state = by_state.nlargest(10, "revenue").iloc[::-1]
        fig = go.Figure(go.Bar(
            x=by_state["revenue"], y=by_state["customer_state"], orientation="h", marker_color=BLUE,
            hovertemplate="<b>%{y}</b><br>R$%{x:,.0f}<extra></extra>",
        ))
        show(style(fig, height=300, xaxis_tickprefix="R$", xaxis_tickformat="~s"))

    st.markdown("##### Category performance")
    cumulative = cat["share"].cumsum()
    top_n_80 = int((cumulative < 80).sum() + 1)
    st.caption(f"{len(cat)} categories sold in the selection; the top {top_n_80} generate 80% of net revenue."
               + (f" The selected category, {category_sel}, ranks #{int(cat.index[cat['category'] == category_sel][0]) + 1}."
                  if category_mode and (cat["category"] == category_sel).any() else ""))
    left, right = st.columns([3, 2])
    with left:
        st.dataframe(
            cat[["category", "revenue", "share", "orders", "items", "avg_item_price", "review"]].head(15),
            hide_index=True, width="stretch", height=422,
            column_config={
                "category": "Category",
                "revenue": st.column_config.NumberColumn("Net revenue", format="R$%,.0f"),
                "share": st.column_config.ProgressColumn("Share of revenue", format="%.1f%%", min_value=0,
                                                         max_value=float(cat["share"].max() or 1)),
                "orders": st.column_config.NumberColumn("Orders", format="%,d"),
                "items": st.column_config.NumberColumn("Items", format="%,d"),
                "avg_item_price": st.column_config.NumberColumn("Avg item price", format="R$%.2f"),
                "review": st.column_config.NumberColumn("Avg review", format="%.2f"),
            },
        )
    with right:
        st.markdown("**Category movers**")
        if span < 6:
            st.info("Select 6+ months to compare the last 3 months with the 3 before.")
        else:
            recent, before = months[months.index(end) - 2: months.index(end) + 1], months[months.index(end) - 5: months.index(end) - 2]
            pivot = categories[categories["year_month"].isin(recent + before)].assign(
                window=lambda f: f["year_month"].isin(recent).map({True: "recent", False: "before"})
            ).pivot_table(index="category", columns="window", values="revenue", aggfunc="sum", fill_value=0)
            pivot = pivot[pivot.get("before", 0) >= 20_000] if "before" in pivot else pivot.iloc[0:0]
            if pivot.empty or "recent" not in pivot:
                st.info("Not enough category revenue to compare.")
            else:
                pivot["change"] = 100 * (pivot["recent"] / pivot["before"] - 1)
                movers = pivot.sort_values("change", ascending=False).reset_index()
                st.caption(f"Revenue {recent[0]}–{recent[-1]} vs {before[0]}–{before[-1]} (categories with ≥ R$20K before).")
                st.dataframe(
                    pd.concat([movers.head(4), movers.tail(4)])[["category", "before", "recent", "change"]],
                    hide_index=True, width="stretch",
                    column_config={
                        "category": "Category",
                        "before": st.column_config.NumberColumn("Before", format="R$%,.0f"),
                        "recent": st.column_config.NumberColumn("Recent", format="R$%,.0f"),
                        "change": st.column_config.NumberColumn("Change", format="%+.1f%%"),
                    },
                )

    st.markdown("##### Seller performance")
    if category_mode:
        st.caption("Seller figures cover all categories (the category filter does not apply to sellers).")
    top_decile = max(1, len(sel) // 10)
    st.caption(
        f"{len(sel):,} active sellers; the top 10% ({top_decile:,}) account for "
        f"{m.ratio(sel['revenue'].head(top_decile).sum(), sel['revenue'].sum()):.0%} of net revenue."
    )
    if sizable.empty:
        st.info(f"No seller has {MIN_SELLER_ORDERS}+ orders in this selection.")
    else:
        fig = go.Figure()
        for flag, color, name in ((False, MUTED, "Other sellers"), (True, ORANGE, "Review < 3.8 and late > 10%")):
            part = sizable[sizable["at_risk"] == flag]
            fig.add_trace(go.Scatter(
                x=part["revenue"], y=part["review"], mode="markers", name=name,
                marker=dict(color=color, size=9, line=dict(color="#fcfcfb", width=1.5), opacity=0.85),
                customdata=part[["seller", "orders", "late_pct", "seller_state"]],
                hovertemplate="<b>%{customdata[0]}</b> (%{customdata[3]})<br>Revenue R$%{x:,.0f}<br>"
                              "Orders %{customdata[1]:,}<br>Avg review %{y:.2f}<br>Late %{customdata[2]:.1f}%<extra></extra>",
            ))
        style(fig, height=360, showlegend=True, xaxis_type="log", xaxis_title="Net revenue (BRL, log scale)", xaxis_dtick=1,
              xaxis_tickprefix="R$", xaxis_tickformat="~s", yaxis_title="Avg review score",
              legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, font_color=INK_2))
        st.markdown(f"Revenue vs. satisfaction (sellers with ≥{MIN_SELLER_ORDERS} orders)")
        show(fig)

# ---------------------------------------------------------------- delivery & satisfaction

with delivery:
    c1, c2, c3 = st.columns(3)
    c1.metric("Avg delivery time", fmt_num(current["delivery_days"], "{:.1f} days"),
              help="Purchase to customer delivery, delivered orders with valid dates.")
    c2.metric("Late deliveries", fmt_num(current["late_pct"], "{:.1f}%"))
    c3.metric("Review: on-time vs. late", f"{fmt_num(on_time_review, '{:.2f}')} vs {fmt_num(late_review, '{:.2f}')}")
    if category_mode:
        st.caption(f"Delivery figures for valid orders containing {category_sel}.")

    if buckets.empty:
        st.info("No delivered orders with valid dates in this selection.")
    else:
        left, right = st.columns(2)
        with left:
            st.markdown("##### Average review by delivery delay")
            by_bucket = buckets.groupby("delay_bucket", as_index=False)[["orders", "review_sum", "review_n", "low_review_orders"]].sum()
            by_bucket["review"] = by_bucket["review_sum"] / by_bucket["review_n"].where(by_bucket["review_n"] > 0)
            by_bucket["low_pct"] = 100 * by_bucket["low_review_orders"] / by_bucket["orders"]
            by_bucket["label"] = by_bucket["delay_bucket"].str[3:]
            fig = go.Figure(go.Bar(
                x=by_bucket["label"], y=by_bucket["review"],
                marker_color=[BLUE if b.startswith("0.") else ORANGE for b in by_bucket["delay_bucket"]],
                text=by_bucket["review"].map(lambda v: "" if pd.isna(v) else f"{v:.2f}"), textposition="outside", textfont_color=INK,
                customdata=by_bucket[["orders", "low_pct"]],
                hovertemplate="<b>%{x}</b><br>Avg review %{y:.2f}<br>Orders %{customdata[0]:,}<br>"
                              "1–2 star reviews %{customdata[1]:.0f}%<extra></extra>",
            ))
            show(style(fig, yaxis_range=[0, 5.4], yaxis_title="Avg review (1–5)"))
            st.caption("Blue: delivered on or before the promised date. Orange: late, by calendar days past the promise.")
        with right:
            st.markdown("##### Distribution of delivery outcomes")
            dist = by_bucket.assign(share=100 * by_bucket["orders"] / by_bucket["orders"].sum())
            fig = go.Figure(go.Bar(
                x=dist["label"], y=dist["share"],
                marker_color=[BLUE if b.startswith("0.") else ORANGE for b in dist["delay_bucket"]],
                text=dist["share"].map("{:.1f}%".format), textposition="outside", textfont_color=INK,
                customdata=dist[["orders"]],
                hovertemplate="<b>%{x}</b><br>%{y:.1f}% of delivered orders<br>Orders %{customdata[0]:,}<extra></extra>",
            ))
            show(style(fig, yaxis_ticksuffix="%", yaxis_title="Share of delivered orders",
                       yaxis_range=[0, max(100, dist["share"].max() * 1.15)]))

        st.markdown("##### Late-delivery rate by customer state")
        state_perf = late_src.groupby("customer_state", as_index=False)[
            ["late_orders", "valid_delivery_orders", "delivery_days_sum", "delivery_days_n", "review_sum", "review_n"]
        ].sum()
        state_perf = state_perf[state_perf["valid_delivery_orders"] >= 100]
        if state_perf.empty:
            st.info("No state has 100+ delivered orders in this selection.")
        else:
            state_perf["late_pct"] = 100 * state_perf["late_orders"] / state_perf["valid_delivery_orders"]
            state_perf["days"] = state_perf["delivery_days_sum"] / state_perf["delivery_days_n"]
            state_perf["review"] = state_perf["review_sum"] / state_perf["review_n"]
            state_perf = state_perf.sort_values("late_pct", ascending=False)
            fig = go.Figure(go.Bar(
                x=state_perf["customer_state"], y=state_perf["late_pct"], marker_color=ORANGE,
                customdata=state_perf[["days", "review", "valid_delivery_orders"]],
                hovertemplate="<b>%{x}</b><br>Late %{y:.1f}%<br>Avg delivery %{customdata[0]:.1f} days<br>"
                              "Avg review %{customdata[1]:.2f}<br>Delivered orders %{customdata[2]:,}<extra></extra>",
            ))
            show(style(fig, height=300, yaxis_ticksuffix="%"))
            st.caption("States with at least 100 delivered orders in the selection, sorted by late-delivery rate.")

    st.markdown("##### Sellers to review")
    st.caption(f"Sellers with {MIN_SELLER_ORDERS}+ orders, late rate above 10% and average review below 3.8 — "
               "a screening rule to investigate, not a verdict." + (" All categories." if category_mode else ""))
    left, right = st.columns([3, 2])
    with left:
        if at_risk.empty:
            st.info("No seller meets the screening rule in this selection.")
        else:
            st.dataframe(
                at_risk[["seller", "seller_state", "orders", "revenue", "late_pct", "review"]].head(15),
                hide_index=True, width="stretch",
                column_config={
                    "seller": "Seller", "seller_state": "State",
                    "orders": st.column_config.NumberColumn("Orders", format="%,d"),
                    "revenue": st.column_config.NumberColumn("Revenue", format="R$%,.0f"),
                    "late_pct": st.column_config.NumberColumn("Late %", format="%.1f%%"),
                    "review": st.column_config.NumberColumn("Review", format="%.2f"),
                },
            )
    with right:
        options = sel.head(300)
        if options.empty:
            st.info("No sellers in this selection.")
        else:
            ids = dict(zip(options["seller"] + " · " + options["seller_state"], options["seller_id"]))
            seller_id = ids[st.selectbox("Seller profile (top 300 by revenue)", list(ids))]
            profile, seller_monthly = m.seller_profile(sellers, seller_id)
            a, b = st.columns(2)
            a.metric("Revenue", m.brl(profile["revenue"]))
            b.metric("Orders", f"{profile['orders']:,}")
            a.metric("Late deliveries", fmt_num(profile["late_pct"], "{:.1f}%"))
            b.metric("Avg review", fmt_num(profile["review"], "{:.2f}"))
            fig = go.Figure(go.Bar(x=seller_monthly["year_month"], y=seller_monthly["revenue"], marker_color=BLUE,
                                   hovertemplate="<b>%{x}</b><br>R$%{y:,.0f}<extra></extra>"))
            show(style(fig, height=180, yaxis_tickprefix="R$", yaxis_tickformat="~s"))

# ---------------------------------------------------------------- business insights

with insights:
    valid_orders = orders[orders["is_valid_order"]]
    state_rev = valid_orders.groupby("customer_state")["revenue"].sum().sort_values(ascending=False)
    top_state, top_state_share = (state_rev.index[0], state_rev.iloc[0] / state_rev.sum()) if len(state_rev) else ("–", 0)
    worst_month = late_month.loc[late_month["late_pct"].idxmax()] if len(late_month) else None
    top3 = cat.head(3)
    st.caption("Calculated live from the current filters. Evidence is observed in historical data; hypotheses are "
               "explanations to test, not proven causes.")

    card("1. Late deliveries go together with much lower reviews", [
        ("Evidence", f"On-time orders average {fmt_num(on_time_review, '{:.2f}')}/5; late orders "
                     f"{fmt_num(late_review, '{:.2f}')}/5, and the gap widens with each extra day late."),
        ("Hypothesis", "Lateness itself lowers satisfaction — but seller, product and region also differ between late and on-time orders."),
        ("Recommendation", "Compare like-for-like (same seller and category) and A/B test more conservative promised dates in high-late states."),
        ("KPI to track", "Weekly late rate; average review on-time vs late; share of 1–2 star reviews."),
    ])
    if worst_month is not None:
        card("2. Delivery reliability drops in some months", [
            ("Evidence", f"The late rate peaked at {worst_month['late_pct']:.1f}% in {worst_month['year_month']} "
                         f"vs {current['late_pct']:.1f}% for the selection."),
            ("Hypothesis", "Carrier and seller capacity do not scale with peak volume (volume alone does not explain Feb–Mar 2018)."),
            ("Recommendation", "Alert when the weekly late rate exceeds twice its 8-week median; review carriers and sellers before peaks."),
            ("KPI to track", "Weekly late rate; late rate by seller state in peak weeks."),
        ])
    card("3. Revenue is concentrated", [
        ("Evidence", f"Top 3 categories ({', '.join(top3['category'])}) bring {top3['share'].sum():.0f}% of net revenue; "
                     f"{top_state} accounts for {top_state_share:.0%}."),
        ("Hypothesis", "Stock-outs or delivery problems in these categories and states would affect the largest share of sales."),
        ("Recommendation", "Monitor availability and delivery for the top categories and states first."),
        ("KPI to track", "Revenue share of top 3 categories and top state; their late rate."),
    ])
    card("4. A short list of sizable sellers combines late deliveries and low ratings", [
        ("Evidence", f"{len(at_risk)} sellers with {MIN_SELLER_ORDERS}+ orders: late rate above 10% and average review below 3.8, "
                     f"holding {m.brl(at_risk['revenue'].sum())} of revenue."),
        ("Hypothesis", "Some of them hand orders to carriers late; others may sell products with quality issues."),
        ("Recommendation", "Check hand-over time against the shipping limit and read review comments before acting."),
        ("KPI to track", "Number of sellers meeting the screen, quarter over quarter."),
    ])

    st.markdown("##### Suggested weekly KPI scorecard")
    st.caption("Values: selected period. Trend: last month in the selection vs. the month before.")
    last_two = monthly.tail(2)
    lm = late_month.tail(2)

    def trend(series: pd.Series, points: bool = False) -> str:
        if len(series) < 2 or not series.iloc[0] or series.isna().any():
            return "–"
        if points:
            return f"{series.iloc[1] - series.iloc[0]:+.1f} pp"
        return f"{(series.iloc[1] / series.iloc[0] - 1):+.1%}"

    scorecard = pd.DataFrame([
        ("Net revenue", m.brl(current["revenue"]), trend(last_two["revenue"]), "Are we growing?"),
        ("Orders", f"{current['orders']:,.0f}", trend(last_two["orders"]), "Demand volume"),
        ("Average order value", m.brl(current["aov"]), trend(last_two["aov"]), "Basket size / pricing"),
        ("Freight as % of revenue", fmt_num(current.get("freight_pct"), "{:.1f}%"), "–", "Shipping cost pressure"),
        ("Late-delivery rate", fmt_num(current["late_pct"], "{:.1f}%"), trend(lm["late_pct"], points=True), "Early warning for reviews"),
        ("Customer satisfaction", fmt_num(current["review"], "{:.2f}"), "–", "Average review score"),
        ("Sellers to review", f"{len(at_risk)}", "–", "Account-management follow-up list"),
    ], columns=["KPI", "Value", "Last month vs. prior", "Why it matters"])
    st.dataframe(scorecard, hide_index=True, width="stretch")

# ---------------------------------------------------------------- methodology & data quality

with method:
    left, right = st.columns(2)
    with left:
        st.markdown("##### Data")
        st.markdown(
            f"- **Source:** Brazilian E-Commerce Public Dataset by Olist (Kaggle), CC BY-NC-SA 4.0 — attribution, non-commercial use.\n"
            f"- **Period covered:** {period} (complete months: Jan 2017 – Aug 2018).\n"
            f"- **Snapshot generated:** {exported or 'n/a'} — historical data, not refreshed in real time.\n"
            "- **Size:** 9 CSV files, ≈1.55M rows (99,441 orders, 112,650 items, 103,886 payments, 1M geolocation samples).\n"
            "- **This app** reads small additive aggregates (< 1 MB) exported from the warehouse; no database or personal data is queried at runtime."
        )
        st.markdown("##### Architecture")
        st.markdown(
            "1. **Load** — Python loads the CSVs into PostgreSQL `raw` tables with typed columns and PK/FK/CHECK constraints.\n"
            "2. **Clean** — `staging`: category fallbacks, one row per ZIP, delivery-date validity flags.\n"
            "3. **Model** — `analytics` star schema: 5 dimensions, 3 facts at order, item and payment grain.\n"
            "4. **Validate** — automated quality and reconciliation checks (below) and 60+ tests in CI.\n"
            "5. **Serve** — Power BI report and this app, both reproducing the same SQL KPIs."
        )
    with right:
        st.markdown("##### Grain")
        st.dataframe(pd.DataFrame([
            ("fact_orders", "One order", "Revenue, orders, AOV, delivery, reviews"),
            ("fact_order_items", "One item in an order", "Category and seller breakdowns"),
            ("fact_payments", "One payment", "Payment methods"),
            ("dim_customer", "One person (customer_unique_id)", "Customer geography, repeat behaviour"),
        ], columns=["Table", "One row per", "Used for"]), hide_index=True, width="stretch")

    st.markdown("##### KPI definitions")
    st.dataframe(pd.DataFrame([
        ("Net revenue", "Σ item price", "Valid orders (not canceled/unavailable); excludes freight", "Order"),
        ("Orders", "Count of orders", "Valid orders", "Order"),
        ("Average order value", "Net revenue ÷ orders", "Valid orders", "Order"),
        ("Customer satisfaction", "Average review score", "Reviewed orders", "Order"),
        ("Late deliveries", "Late ÷ measurable deliveries", "Delivered, valid dates; late = later calendar day than promised", "Order"),
        ("Avg delivery time", "Purchase → delivery days", "Delivered, valid dates", "Order"),
        ("Category revenue", "Σ item price per category", "Valid orders", "Item"),
        ("Seller revenue", "Σ item price per seller", "Valid orders", "Item"),
    ], columns=["KPI", "Formula", "Population", "Grain"]), hide_index=True, width="stretch")

    st.markdown("##### Data quality checks (run on every rebuild)")
    if quality:
        q = pd.DataFrame(quality)
        counts = q["status"].value_counts()
        a, b, c = st.columns(3)
        a.metric("Passed", int(counts.get("PASS", 0)))
        b.metric("Warnings (documented)", int(counts.get("WARN", 0)))
        c.metric("Failed", int(counts.get("FAIL", 0)))
        st.dataframe(q[["status", "category", "description", "value"]].sort_values("status", ascending=False),
                     hide_index=True, width="stretch", height=320,
                     column_config={"status": "Status", "category": "Area", "description": "Check",
                                    "value": st.column_config.NumberColumn("Value", format="%.4g")})
    else:
        st.info("Quality summary not available in this export.")

    st.markdown("##### Reconciliation: this app vs. the SQL warehouse (full dataset, no filters)")
    full = m.kpis(data["orders"])
    st.dataframe(pd.DataFrame([
        ("Net revenue", m.brl(reference.get("net_revenue"), 3), m.brl(full["revenue"], 3)),
        ("Valid orders", f"{reference.get('total_orders', 0):,.0f}", f"{full['orders']:,.0f}"),
        ("Average order value", f"R${reference.get('avg_order_value', 0):,.2f}", f"R${full['aov']:,.2f}"),
        ("Late-delivery rate", f"{reference.get('late_delivery_rate_pct', 0):.2f}%", f"{full['late_pct']:.2f}%"),
        ("Average review score", f"{reference.get('avg_review_score', 0):.2f}", f"{full['review']:.2f}"),
    ], columns=["KPI", "SQL (reporting.vw_executive_summary)", "This app"]), hide_index=True, width="stretch")

    st.markdown("##### Limitations")
    st.markdown(
        "- Historical, anonymized public data; no costs or margins, so profitability cannot be measured; no carrier field.\n"
        "- Delay-vs-review results are observational associations, not causal estimates.\n"
        "- Customer location = ZIP of the customer's most recent order; 268 customers have a ZIP missing from the public geolocation file ('Unknown').\n"
        "- Category filter is single-select; seller figures are not split by category.\n"
        f"- Independent portfolio project, not affiliated with or endorsed by Olist. Code (MIT) and docs: [{REPO_URL}]({REPO_URL})."
    )
