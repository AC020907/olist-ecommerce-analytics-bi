"""Sales Analytics & BI Dashboard -- client-facing demo built on the Olist warehouse.

Reads only the pre-aggregates in demo/data/ (written by `python -m olist_bi export`),
so it needs no database and reproduces the SQL KPI definitions exactly:
revenue / orders / AOV use valid orders (not canceled/unavailable); delivery and
review KPIs use all orders, as in reporting.vw_executive_summary.

Run:  streamlit run demo/app.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent / "data"
ANALYSIS_WINDOW = ("2017-01", "2018-08")

BLUE = "#2a78d6"
ORANGE = "#eb6834"
MUTED = "#a3a29c"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e8e7e3"

st.set_page_config(page_title="Sales Analytics & BI Demo", page_icon=":bar_chart:", layout="wide")

st.markdown(
    """
<style>
.block-container {padding-top: 2rem; max-width: 1280px;}
[data-testid="stMetric"] {background: #ffffff; border: 1px solid #e8e7e3; border-radius: 10px; padding: 14px 16px;}
[data-testid="stMetricLabel"] p {color: #52514e; font-size: 0.85rem;}
[data-testid="stMetricValue"] {font-size: 1.6rem;}
.eyebrow {color: #2a78d6; font-weight: 600; letter-spacing: .04em; text-transform: uppercase; font-size: .78rem; margin-bottom: .2rem;}
.lede {color: #52514e; font-size: 1.02rem; max-width: 820px;}
.note {color: #52514e; font-size: .85rem;}
.insight {background: #ffffff; border: 1px solid #e8e7e3; border-left: 4px solid #2a78d6; border-radius: 8px; padding: 14px 16px; margin-bottom: 12px;}
.insight h4 {margin: 0 0 6px 0; font-size: 1rem;}
.insight p {margin: 0; color: #303030; font-size: .93rem;}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- data

@st.cache_data
def load() -> dict[str, pd.DataFrame | dict]:
    frames = {name: pd.read_parquet(DATA_DIR / f"{name}.parquet") for name in ("orders", "categories", "sellers", "delivery_buckets")}
    for name in ("categories",):
        frames[name]["category"] = frames[name]["category"].str.replace("_", " ")
    frames["reference"] = json.loads((DATA_DIR / "kpi_reference.json").read_text(encoding="utf-8"))
    return frames


def brl(value: float, decimals: int = 2) -> str:
    if pd.isna(value):
        return "–"
    if abs(value) >= 1e6:
        return f"R${value / 1e6:,.{decimals}f}M"
    if abs(value) >= 1e3:
        return f"R${value / 1e3:,.0f}K"
    return f"R${value:,.2f}"


def ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else float("nan")


def kpis(orders: pd.DataFrame) -> dict[str, float]:
    valid = orders[orders["is_valid_order"]]
    return {
        "revenue": valid["revenue"].sum(),
        "orders": valid["orders"].sum(),
        "aov": ratio(valid["revenue"].sum(), valid["orders"].sum()),
        "freight_pct": 100 * ratio(valid["freight"].sum(), valid["revenue"].sum()),
        "review": ratio(orders["review_sum"].sum(), orders["review_n"].sum()),
        "late_pct": 100 * ratio(orders["late_orders"].sum(), orders["valid_delivery_orders"].sum()),
        "delivery_days": ratio(orders["delivery_days_sum"].sum(), orders["delivery_days_n"].sum()),
    }


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


data = load()
months = sorted(data["orders"]["year_month"].unique())

# ---------------------------------------------------------------- filters

with st.sidebar:
    st.markdown("### Filters")
    start, end = st.select_slider(
        "Order month",
        options=months,
        value=ANALYSIS_WINDOW,
        help="Default is Jan 2017 – Aug 2018, the window with complete monthly data. "
             "Sep 2016–Dec 2016 and Sep–Oct 2018 are partial edges of the public dataset.",
    )
    regions = sorted(data["orders"]["customer_region"].unique())
    region_sel = st.multiselect("Customer region", regions, placeholder="All regions")
    state_options = sorted(
        data["orders"].loc[data["orders"]["customer_region"].isin(region_sel or regions), "customer_state"].unique()
    )
    state_sel = st.multiselect("Customer state", state_options, placeholder="All states")
    st.divider()
    st.markdown(
        "<p class='note'>Data: public Olist Brazilian e-commerce dataset (99,441 orders, 2016–2018). "
        "This is an independent portfolio project, not work commissioned by Olist.</p>",
        unsafe_allow_html=True,
    )


def apply_filters(frame: pd.DataFrame, month_from: str = None, month_to: str = None) -> pd.DataFrame:
    month_from, month_to = month_from or start, month_to or end
    mask = frame["year_month"].between(month_from, month_to)
    if region_sel:
        mask &= frame["customer_region"].isin(region_sel)
    if state_sel:
        mask &= frame["customer_state"].isin(state_sel)
    return frame[mask]


orders = apply_filters(data["orders"])
categories = apply_filters(data["categories"])
sellers = apply_filters(data["sellers"])
buckets = apply_filters(data["delivery_buckets"])
current = kpis(orders)

# Comparison period of equal length immediately before the selection, only when it
# stays inside the complete-data window (otherwise growth vs. a partial month is noise).
span = months.index(end) - months.index(start) + 1
prev_start_idx = months.index(start) - span
previous = None
if prev_start_idx >= 0 and months[prev_start_idx] >= ANALYSIS_WINDOW[0]:
    previous = kpis(apply_filters(data["orders"], months[prev_start_idx], months[months.index(start) - 1]))


def delta(key: str, fmt: str = "{:+.1f}%", relative: bool = True) -> str | None:
    if previous is None or pd.isna(previous[key]) or not previous[key]:
        return None
    change = (current[key] / previous[key] - 1) * 100 if relative else current[key] - previous[key]
    return fmt.format(change)


# ---------------------------------------------------------------- header

st.markdown("<div class='eyebrow'>Sales Analytics &amp; Business Intelligence · Live demo</div>", unsafe_allow_html=True)
st.title("From raw order data to a dashboard you can run the business on")
st.markdown(
    "<p class='lede'>This demo shows the kind of dashboard I build for e-commerce teams: "
    "validated revenue numbers, sales drivers, delivery problems and their effect on customer "
    "satisfaction, all from one reconciled data model. It runs on the public Olist dataset "
    "(Brazilian marketplace, 2016–2018); with your data, the same pipeline and views apply.</p>",
    unsafe_allow_html=True,
)

overview, sales, delivery, insights, method = st.tabs(
    ["Executive overview", "Sales performance", "Delivery & satisfaction", "Insights & weekly KPIs", "How the numbers are built"]
)

# ---------------------------------------------------------------- executive overview

with overview:
    if previous is None:
        st.caption(f"{start} → {end} · growth deltas appear when an equal-length prior period inside the complete-data window exists.")
    else:
        st.caption(f"{start} → {end} · deltas compare with the previous {span} month(s).")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Net revenue", brl(current["revenue"]), delta("revenue"),
              help="Sum of item prices on orders that were not canceled or unavailable. Excludes freight.")
    c2.metric("Orders", f"{current['orders']:,.0f}", delta("orders"))
    c3.metric("Average order value", brl(current["aov"]), delta("aov"))
    c4.metric("Avg review score", f"{current['review']:.2f} / 5", delta("review", "{:+.2f}", relative=False))
    c5.metric("Late deliveries", f"{current['late_pct']:.1f}%", delta("late_pct", "{:+.1f} pp", relative=False),
              delta_color="inverse", help="Delivered after the date promised to the customer, among delivered orders with valid dates.")

    monthly = (
        orders[orders["is_valid_order"]].groupby("year_month", as_index=False)[["revenue", "orders"]].sum()
    )
    monthly["aov"] = monthly["revenue"] / monthly["orders"]

    left, right = st.columns([2, 1])
    with left:
        st.markdown("##### Monthly net revenue")
        fig = go.Figure(go.Bar(
            x=monthly["year_month"], y=monthly["revenue"], marker_color=BLUE,
            customdata=monthly[["orders", "aov"]],
            hovertemplate="<b>%{x}</b><br>Revenue R$%{y:,.0f}<br>Orders %{customdata[0]:,}<br>AOV R$%{customdata[1]:,.2f}<extra></extra>",
        ))
        show(style(fig, yaxis_tickprefix="R$", yaxis_tickformat="~s"))
    with right:
        st.markdown("##### Average order value")
        fig = go.Figure(go.Scatter(
            x=monthly["year_month"], y=monthly["aov"], mode="lines+markers",
            line=dict(color=BLUE, width=2), marker=dict(size=7),
            hovertemplate="<b>%{x}</b><br>AOV R$%{y:,.2f}<extra></extra>",
        ))
        show(style(fig, yaxis_tickprefix="R$"))

    left, right = st.columns(2)
    with left:
        st.markdown("##### Top 10 categories by net revenue")
        top = categories.groupby("category", as_index=False)["revenue"].sum().nlargest(10, "revenue").iloc[::-1]
        fig = go.Figure(go.Bar(
            x=top["revenue"], y=top["category"], orientation="h", marker_color=BLUE,
            hovertemplate="<b>%{y}</b><br>R$%{x:,.0f}<extra></extra>",
        ))
        show(style(fig, xaxis_tickprefix="R$", xaxis_tickformat="~s"))
    with right:
        st.markdown("##### Net revenue by customer state")
        by_state = orders[orders["is_valid_order"]].groupby("customer_state", as_index=False)["revenue"].sum()
        by_state = by_state.nlargest(10, "revenue").iloc[::-1]
        fig = go.Figure(go.Bar(
            x=by_state["revenue"], y=by_state["customer_state"], orientation="h", marker_color=BLUE,
            hovertemplate="<b>%{y}</b><br>R$%{x:,.0f}<extra></extra>",
        ))
        show(style(fig, xaxis_tickprefix="R$", xaxis_tickformat="~s"))

# ---------------------------------------------------------------- sales performance

with sales:
    st.markdown("##### Category performance")
    cat = categories.groupby("category", as_index=False)[["revenue", "items", "orders", "review_sum", "review_n"]].sum()
    total_revenue = cat["revenue"].sum()
    cat["share"] = 100 * cat["revenue"] / total_revenue
    cat["avg_item_price"] = cat["revenue"] / cat["items"]
    cat["review"] = cat["review_sum"] / cat["review_n"]
    cat = cat.sort_values("revenue", ascending=False)
    cat["cumulative_share"] = cat["share"].cumsum()
    top_n_80 = int((cat["cumulative_share"] < 80).sum() + 1)
    st.caption(
        f"{len(cat)} categories sold in the selection; the top {top_n_80} generate 80% of net revenue."
    )
    st.dataframe(
        cat[["category", "revenue", "share", "orders", "items", "avg_item_price", "review"]].head(15),
        hide_index=True, width="stretch", height=422,
        column_config={
            "category": "Category",
            "revenue": st.column_config.NumberColumn("Net revenue", format="R$%,.0f"),
            "share": st.column_config.ProgressColumn("Share of revenue", format="%.1f%%", min_value=0, max_value=float(cat["share"].max() or 1)),
            "orders": st.column_config.NumberColumn("Orders", format="%,d"),
            "items": st.column_config.NumberColumn("Items", format="%,d"),
            "avg_item_price": st.column_config.NumberColumn("Avg item price", format="R$%.2f"),
            "review": st.column_config.NumberColumn("Avg review", format="%.2f"),
        },
    )

    st.markdown("##### Seller performance")
    sel = sellers.groupby(["seller_id", "seller_state"], as_index=False)[
        ["revenue", "orders", "items", "late_orders", "valid_delivery_orders", "review_sum", "review_n"]
    ].sum()
    sel["late_pct"] = 100 * sel["late_orders"] / sel["valid_delivery_orders"].where(sel["valid_delivery_orders"] > 0)
    sel["review"] = sel["review_sum"] / sel["review_n"].where(sel["review_n"] > 0)
    sel = sel.sort_values("revenue", ascending=False)
    sel["seller"] = "Seller " + sel["seller_id"].str[:8]
    top_decile = max(1, len(sel) // 10)
    st.caption(
        f"{len(sel):,} active sellers; the top 10% ({top_decile:,}) account for "
        f"{sel['revenue'].head(top_decile).sum() / sel['revenue'].sum():.0%} of net revenue."
    )

    left, right = st.columns([3, 2])
    with left:
        min_orders = 30
        sizable = sel[sel["orders"] >= min_orders].copy()
        sizable["at_risk"] = (sizable["review"] < 3.8) & (sizable["late_pct"] > 10)
        st.markdown(f"Revenue vs. satisfaction (sellers with ≥{min_orders} orders)")
        fig = go.Figure()
        for flag, color, name in ((False, MUTED, "Other sellers"), (True, ORANGE, "At risk: review < 3.8 and late > 10%")):
            part = sizable[sizable["at_risk"] == flag]
            fig.add_trace(go.Scatter(
                x=part["revenue"], y=part["review"], mode="markers", name=name,
                marker=dict(color=color, size=9, line=dict(color="#fcfcfb", width=1.5), opacity=0.85),
                customdata=part[["seller", "orders", "late_pct", "seller_state"]],
                hovertemplate="<b>%{customdata[0]}</b> (%{customdata[3]})<br>Revenue R$%{x:,.0f}<br>"
                              "Orders %{customdata[1]:,}<br>Avg review %{y:.2f}<br>Late %{customdata[2]:.1f}%<extra></extra>",
            ))
        style(fig, height=380, showlegend=True, xaxis_type="log", xaxis_title="Net revenue (log scale)", xaxis_dtick=1,
              xaxis_tickprefix="R$", xaxis_tickformat="~s",
              yaxis_title="Avg review score",
              legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, font_color=INK_2))
        show(fig)
    with right:
        at_risk = sizable[sizable["at_risk"]].sort_values("revenue", ascending=False)
        st.markdown(f"**{len(at_risk)} high-volume sellers at risk**, holding {brl(at_risk['revenue'].sum())} of revenue")
        st.dataframe(
            at_risk[["seller", "seller_state", "revenue", "late_pct", "review"]].head(12),
            hide_index=True, width="stretch",
            column_config={
                "seller": "Seller", "seller_state": "State",
                "revenue": st.column_config.NumberColumn("Revenue", format="R$%,.0f"),
                "late_pct": st.column_config.NumberColumn("Late %", format="%.1f%%"),
                "review": st.column_config.NumberColumn("Review", format="%.2f"),
            },
        )

# ---------------------------------------------------------------- delivery & satisfaction

with delivery:
    c1, c2, c3 = st.columns(3)
    c1.metric("Avg delivery time", f"{current['delivery_days']:.1f} days", help="Purchase to customer delivery, delivered orders with valid dates.")
    c2.metric("Late deliveries", f"{current['late_pct']:.1f}%")
    on_time = buckets[buckets["delay_bucket"].str.startswith("0.")]
    late = buckets[~buckets["delay_bucket"].str.startswith("0.")]
    on_time_review = ratio(on_time["review_sum"].sum(), on_time["review_n"].sum())
    late_review = ratio(late["review_sum"].sum(), late["review_n"].sum())
    c3.metric("Review: on-time vs. late", f"{on_time_review:.2f} vs {late_review:.2f}")

    left, right = st.columns(2)
    with left:
        st.markdown("##### Average review by delivery delay")
        by_bucket = buckets.groupby("delay_bucket", as_index=False)[["orders", "review_sum", "review_n", "low_review_orders"]].sum()
        by_bucket["review"] = by_bucket["review_sum"] / by_bucket["review_n"]
        by_bucket["low_pct"] = 100 * by_bucket["low_review_orders"] / by_bucket["orders"]
        by_bucket["label"] = by_bucket["delay_bucket"].str[3:]
        fig = go.Figure(go.Bar(
            x=by_bucket["label"], y=by_bucket["review"],
            marker_color=[BLUE if b.startswith("0.") else ORANGE for b in by_bucket["delay_bucket"]],
            text=by_bucket["review"].map("{:.2f}".format), textposition="outside", textfont_color=INK,
            customdata=by_bucket[["orders", "low_pct"]],
            hovertemplate="<b>%{x}</b><br>Avg review %{y:.2f}<br>Orders %{customdata[0]:,}<br>"
                          "1–2 star reviews %{customdata[1]:.0f}%<extra></extra>",
        ))
        show(style(fig, yaxis_range=[0, 5.4], yaxis_title="Avg review (1–5)"))
        st.caption("Blue: delivered by the promised date. Orange: late, grouped by days past the promise.")
    with right:
        st.markdown("##### Late-delivery rate by month")
        late_month = orders.groupby("year_month", as_index=False)[["late_orders", "valid_delivery_orders"]].sum()
        late_month["late_pct"] = 100 * late_month["late_orders"] / late_month["valid_delivery_orders"]
        fig = go.Figure(go.Scatter(
            x=late_month["year_month"], y=late_month["late_pct"], mode="lines+markers",
            line=dict(color=ORANGE, width=2), marker=dict(size=7),
            hovertemplate="<b>%{x}</b><br>Late %{y:.1f}%<extra></extra>",
        ))
        show(style(fig, yaxis_ticksuffix="%", yaxis_rangemode="tozero"))
        st.caption("Across the full dataset, peaks follow demand spikes (Black Friday Nov 2017, Feb–Mar 2018).")

    st.markdown("##### Late-delivery rate by customer state")
    state_perf = orders.groupby("customer_state", as_index=False)[
        ["orders", "late_orders", "valid_delivery_orders", "delivery_days_sum", "delivery_days_n", "review_sum", "review_n"]
    ].sum()
    state_perf = state_perf[state_perf["valid_delivery_orders"] >= 100]
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

# ---------------------------------------------------------------- insights & weekly KPIs

with insights:
    valid_orders = orders[orders["is_valid_order"]]
    state_rev = valid_orders.groupby("customer_state")["revenue"].sum().sort_values(ascending=False)
    top_state, top_state_share = (state_rev.index[0], state_rev.iloc[0] / state_rev.sum()) if len(state_rev) else ("–", 0)
    worst_month = late_month.loc[late_month["late_pct"].idxmax()] if len(late_month) else None
    top3 = cat.head(3)

    findings = [
        ("Late deliveries are strongly associated with bad reviews",
         f"Orders delivered on time average {on_time_review:.2f}/5; late orders average {late_review:.2f}/5. "
         "Satisfaction falls further the later the order arrives, so delivery promises are a customer-experience lever, not just a logistics metric."),
        ("Delivery reliability breaks during demand peaks",
         f"The late-delivery rate peaked at {worst_month['late_pct']:.1f}% in {worst_month['year_month']} "
         f"versus {current['late_pct']:.1f}% for the selected period overall. Peak-season capacity and promised dates should be planned together."
         if worst_month is not None else "No delivered orders in the selection."),
        ("Where the revenue comes from",
         f"The top 3 categories ({', '.join(top3['category'].str.replace('_', ' '))}) bring {top3['share'].sum():.0f}% of net revenue; "
         f"{top_state} alone accounts for {top_state_share:.0%}. These are the categories and markets where stock-outs or delivery problems would cost the most."),
        ("A small group of high-volume sellers combines poor delivery and low ratings",
         f"{len(at_risk)} sellers with 30+ orders have both a late rate above 10% and an average review below 3.8, "
         f"holding {brl(at_risk['revenue'].sum())} of revenue. They are a short, actionable list for account management."),
    ]
    st.markdown("##### What the data says")
    for title, body in findings:
        st.markdown(f"<div class='insight'><h4>{title}</h4><p>{body}</p></div>", unsafe_allow_html=True)

    st.markdown("##### Suggested weekly KPI scorecard")
    st.caption("What I would put in front of an e-commerce manager every Monday. Values: selected period; trend: last month in the selection vs. the month before.")
    last_two = monthly.tail(2)
    lm = late_month.tail(2)

    def trend(series: pd.Series, points: bool = False) -> str:
        if len(series) < 2 or not series.iloc[0]:
            return "–"
        if points:
            return f"{series.iloc[1] - series.iloc[0]:+.1f} pp"
        return f"{(series.iloc[1] / series.iloc[0] - 1):+.1%}"

    scorecard = pd.DataFrame([
        ("Net revenue", brl(current["revenue"]), trend(last_two["revenue"]), "Are we growing?"),
        ("Orders", f"{current['orders']:,.0f}", trend(last_two["orders"]), "Demand volume"),
        ("Average order value", brl(current["aov"]), trend(last_two["aov"]), "Basket size / pricing"),
        ("Freight as % of revenue", f"{current['freight_pct']:.1f}%", "–", "Shipping cost pressure on margin"),
        ("Late-delivery rate", f"{current['late_pct']:.1f}%", trend(lm["late_pct"], points=True), "Early warning for review scores"),
        ("Average review score", f"{current['review']:.2f}", "–", "Customer satisfaction"),
        ("Sellers at risk", f"{len(at_risk)}", "–", "Account-management follow-up list"),
    ], columns=["KPI", "Value", "Last month vs. prior", "Why it matters"])
    st.dataframe(scorecard, hide_index=True, width="stretch")

    st.markdown("##### Limitations")
    st.markdown(
        "- Public, anonymized dataset; no costs or margins, so profitability cannot be measured.\n"
        "- The relationship between delays and reviews is observational: it shows association, not proven causation.\n"
        "- Revenue = item prices on valid orders (excludes freight and canceled/unavailable orders).\n"
        "- Customer location is the customer's most recent address; 268 customers have a ZIP prefix missing from the public geolocation file."
    )

# ---------------------------------------------------------------- method

with method:
    ref = data["reference"]
    st.markdown("##### Pipeline")
    st.markdown(
        "1. **Load** — 9 raw CSV files (≈1.5M rows) into PostgreSQL `raw` tables with typed columns and PK/FK/CHECK constraints.\n"
        "2. **Clean** — `staging` layer: category translation fallbacks, one row per ZIP from 1M geolocation samples, delivery-date validity flags.\n"
        "3. **Model** — `analytics` star schema: 5 dimensions and 3 fact tables at order, item and payment grain, so multi-item / multi-payment orders never double-count revenue.\n"
        "4. **Validate** — 42 automated data-quality and reconciliation checks (keys, nulls, dates, money, cross-grain revenue totals).\n"
        "5. **Serve** — Power BI semantic model (6-page dashboard) and this web demo, both reading the same definitions."
    )
    st.markdown("##### Reconciliation: this demo vs. the SQL warehouse (full dataset, no filters)")
    full = kpis(data["orders"])
    recon = pd.DataFrame([
        ("Net revenue", brl(ref["net_revenue"], 3), brl(full["revenue"], 3)),
        ("Valid orders", f"{ref['total_orders']:,.0f}", f"{full['orders']:,.0f}"),
        ("Average order value", f"R${ref['avg_order_value']:,.2f}", f"R${full['aov']:,.2f}"),
        ("Late-delivery rate", f"{ref['late_delivery_rate_pct']:.2f}%", f"{full['late_pct']:.2f}%"),
        ("Average review score", f"{ref['avg_review_score']:.2f}", f"{full['review']:.2f}"),
    ], columns=["KPI", "SQL (reporting.vw_executive_summary)", "This demo"])
    st.dataframe(recon, hide_index=True, width="stretch")
    st.caption("The demo reads additive pre-aggregates exported from the warehouse, so every filter combination re-aggregates to the same definitions used in SQL and Power BI.")
