"""Sales Analytics & BI Dashboard -- client-facing demo built on the Olist warehouse.

Reads only the pre-aggregates in demo/data/ (written by `python -m olist_bi export`),
so it needs no database. KPI logic lives in metrics.py and mirrors the SQL views:
revenue / orders / AOV use valid orders (not canceled/unavailable); review score uses
all reviewed orders; late rate = delivered on a later calendar day than promised,
over delivered orders with valid dates.

Run:  streamlit run demo/app.py
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import metrics as m

BLUE = "#2a78d6"
ORANGE = "#eb6834"
MUTED = "#a3a29c"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e8e7e3"
MIN_SELLER_ORDERS = 30

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
.insight .label {color: #52514e; font-weight: 600;}
@media (max-width: 640px) {
  .block-container {padding-left: 1rem; padding-right: 1rem; padding-top: 3.5rem;}
  h1 {font-size: 1.7rem !important;}
}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def load() -> tuple[dict[str, pd.DataFrame], dict, dict]:
    return m.load_frames(), m.load_json("kpi_reference.json"), m.load_json("export_metadata.json")


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


data, reference, metadata = load()
months = sorted(data["orders"]["year_month"].unique())

# ---------------------------------------------------------------- filters

with st.sidebar:
    st.markdown("### Filters")
    start, end = st.select_slider(
        "Order month",
        options=months,
        value=m.ANALYSIS_WINDOW,
        help="Default is Jan 2017 – Aug 2018, the window with complete monthly data. "
             "Sep–Dec 2016 and Sep–Oct 2018 are partial edges of the public dataset.",
    )
    regions = sorted(data["orders"]["customer_region"].unique())
    region_sel = st.multiselect("Customer region", regions, placeholder="All regions",
                                help="'Unknown' = customers whose ZIP prefix is missing from the public geolocation file.")
    state_options = sorted(
        data["orders"].loc[data["orders"]["customer_region"].isin(region_sel or regions), "customer_state"].unique()
    )
    state_sel = st.multiselect("Customer state", state_options, placeholder="All states")
    st.divider()
    period = f"{metadata.get('first_order_date', '2016-09-04')} to {metadata.get('last_order_date', '2018-10-17')}"
    exported = metadata.get("exported_on")
    st.markdown(
        f"<p class='note'><b>Historical snapshot, not live data.</b> Orders from {period} "
        f"(public Olist Brazilian e-commerce dataset, CC BY-NC-SA 4.0)."
        + (f" Aggregates exported from the warehouse on {exported}." if exported else "")
        + " Independent portfolio project, not commissioned by Olist.</p>",
        unsafe_allow_html=True,
    )


def apply_filters(frame: pd.DataFrame, month_from: str | None = None, month_to: str | None = None) -> pd.DataFrame:
    return m.apply_filters(frame, month_from or start, month_to or end, region_sel, state_sel)


orders = apply_filters(data["orders"])
categories = apply_filters(data["categories"])
sellers = apply_filters(data["sellers"])
buckets = apply_filters(data["delivery_buckets"])
current = m.kpis(orders)

# ---------------------------------------------------------------- header

st.markdown("<div class='eyebrow'>Sales Analytics &amp; Business Intelligence · Interactive demo</div>", unsafe_allow_html=True)
st.title("From raw order data to a dashboard you can run the business on")
st.markdown(
    "<p class='lede'>This demo shows the kind of dashboard I build for e-commerce teams: "
    "validated revenue numbers, sales drivers, delivery problems and how they relate to customer "
    "satisfaction, all from one reconciled data model. It runs on the public Olist dataset "
    "(Brazilian marketplace, 2016–2018); with your data, the same pipeline and views apply.</p>",
    unsafe_allow_html=True,
)

if current["orders"] == 0:
    st.warning("No valid orders match these filters. Widen the month range or clear the region/state filters.")
    st.stop()

# Comparison period of equal length immediately before the selection, only when it
# stays inside the complete-data window (otherwise growth vs. a partial month is noise).
span = months.index(end) - months.index(start) + 1
prev_start_idx = months.index(start) - span
previous = None
if prev_start_idx >= 0 and months[prev_start_idx] >= m.ANALYSIS_WINDOW[0]:
    previous = m.kpis(apply_filters(data["orders"], months[prev_start_idx], months[months.index(start) - 1]))


def delta(key: str, fmt: str = "{:+.1f}%", relative: bool = True) -> str | None:
    if previous is None or pd.isna(previous[key]) or not previous[key] or pd.isna(current[key]):
        return None
    change = (current[key] / previous[key] - 1) * 100 if relative else current[key] - previous[key]
    return fmt.format(change)


def fmt_num(value: float, pattern: str) -> str:
    return "–" if pd.isna(value) else pattern.format(value)


overview, sales, delivery, insights, method = st.tabs(
    ["Executive overview", "Sales performance", "Delivery & satisfaction", "Insights & weekly KPIs", "How the numbers are built"]
)

monthly = orders[orders["is_valid_order"]].groupby("year_month", as_index=False)[["revenue", "orders"]].sum()
monthly["aov"] = monthly["revenue"] / monthly["orders"].where(monthly["orders"] > 0)
late_month = orders.groupby("year_month", as_index=False)[["late_orders", "valid_delivery_orders"]].sum()
late_month = late_month[late_month["valid_delivery_orders"] > 0]
late_month["late_pct"] = 100 * late_month["late_orders"] / late_month["valid_delivery_orders"]
cat = m.category_table(categories)
sel = m.seller_table(sellers)
sel["seller"] = "Seller " + sel["seller_id"].str[:8]
sizable = m.at_risk_sellers(sel, MIN_SELLER_ORDERS)
at_risk = sizable[sizable["at_risk"]].sort_values("revenue", ascending=False)

# ---------------------------------------------------------------- executive overview

with overview:
    if previous is None:
        st.caption(f"{start} → {end} · growth deltas appear when an equal-length prior period inside the complete-data window exists.")
    else:
        st.caption(f"{start} → {end} · deltas compare with the previous {span} month(s).")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Net revenue", m.brl(current["revenue"]), delta("revenue"),
              help="Sum of item prices (BRL) on orders that were not canceled or unavailable. Excludes freight.")
    c2.metric("Orders", f"{current['orders']:,.0f}", delta("orders"))
    c3.metric("Average order value", m.brl(current["aov"]), delta("aov"))
    c4.metric("Avg review score", fmt_num(current["review"], "{:.2f} / 5"), delta("review", "{:+.2f}", relative=False))
    c5.metric("Late deliveries", fmt_num(current["late_pct"], "{:.1f}%"), delta("late_pct", "{:+.1f} pp", relative=False),
              delta_color="inverse",
              help="Delivered on a later calendar day than the date promised to the customer, among delivered orders with valid dates.")

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
        st.markdown("##### Average order value (BRL)")
        fig = go.Figure(go.Scatter(
            x=monthly["year_month"], y=monthly["aov"], mode="lines+markers",
            line=dict(color=BLUE, width=2), marker=dict(size=7),
            hovertemplate="<b>%{x}</b><br>AOV R$%{y:,.2f}<extra></extra>",
        ))
        show(style(fig, yaxis_tickprefix="R$"))

    left, right = st.columns(2)
    with left:
        st.markdown("##### Top 10 categories by net revenue")
        top = cat.head(10).iloc[::-1]
        fig = go.Figure(go.Bar(
            x=top["revenue"], y=top["category"], orientation="h", marker_color=BLUE,
            hovertemplate="<b>%{y}</b><br>R$%{x:,.0f}<extra></extra>",
        ))
        show(style(fig, xaxis_tickprefix="R$", xaxis_tickformat="~s"))
    with right:
        st.markdown("##### Net revenue by customer state (top 10)")
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
    cumulative = cat["share"].cumsum()
    top_n_80 = int((cumulative < 80).sum() + 1)
    st.caption(f"{len(cat)} categories sold in the selection; the top {top_n_80} generate 80% of net revenue.")
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

    st.markdown("##### Seller performance")
    top_decile = max(1, len(sel) // 10)
    st.caption(
        f"{len(sel):,} active sellers; the top 10% ({top_decile:,}) account for "
        f"{m.ratio(sel['revenue'].head(top_decile).sum(), sel['revenue'].sum()):.0%} of net revenue."
    )
    left, right = st.columns([3, 2])
    with left:
        st.markdown(f"Revenue vs. satisfaction (sellers with ≥{MIN_SELLER_ORDERS} orders)")
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
            style(fig, height=380, showlegend=True, xaxis_type="log", xaxis_title="Net revenue (BRL, log scale)", xaxis_dtick=1,
                  xaxis_tickprefix="R$", xaxis_tickformat="~s", yaxis_title="Avg review score",
                  legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, font_color=INK_2))
            show(fig)
    with right:
        st.markdown(f"**{len(at_risk)} high-volume sellers to review**, holding {m.brl(at_risk['revenue'].sum())} of revenue")
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
    on_time = buckets[buckets["delay_bucket"].str.startswith("0.")]
    late = buckets[~buckets["delay_bucket"].str.startswith("0.")]
    on_time_review = m.ratio(on_time["review_sum"].sum(), on_time["review_n"].sum())
    late_review = m.ratio(late["review_sum"].sum(), late["review_n"].sum())
    c1, c2, c3 = st.columns(3)
    c1.metric("Avg delivery time", fmt_num(current["delivery_days"], "{:.1f} days"),
              help="Purchase to customer delivery, delivered orders with valid dates.")
    c2.metric("Late deliveries", fmt_num(current["late_pct"], "{:.1f}%"))
    c3.metric("Review: on-time vs. late", f"{fmt_num(on_time_review, '{:.2f}')} vs {fmt_num(late_review, '{:.2f}')}")

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
            st.markdown("##### Late-delivery rate by month")
            fig = go.Figure(go.Scatter(
                x=late_month["year_month"], y=late_month["late_pct"], mode="lines+markers",
                line=dict(color=ORANGE, width=2), marker=dict(size=7),
                hovertemplate="<b>%{x}</b><br>Late %{y:.1f}%<extra></extra>",
            ))
            show(style(fig, yaxis_ticksuffix="%", yaxis_rangemode="tozero"))
            st.caption("Across the full dataset, the highest late rates coincide with demand peaks (Nov 2017, Feb–Mar 2018).")

        st.markdown("##### Late-delivery rate by customer state")
        state_perf = orders.groupby("customer_state", as_index=False)[
            ["orders", "late_orders", "valid_delivery_orders", "delivery_days_sum", "delivery_days_n", "review_sum", "review_n"]
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

# ---------------------------------------------------------------- insights & weekly KPIs

with insights:
    valid_orders = orders[orders["is_valid_order"]]
    state_rev = valid_orders.groupby("customer_state")["revenue"].sum().sort_values(ascending=False)
    top_state, top_state_share = (state_rev.index[0], state_rev.iloc[0] / state_rev.sum()) if len(state_rev) else ("–", 0)
    worst_month = late_month.loc[late_month["late_pct"].idxmax()] if len(late_month) else None
    top3 = cat.head(3)

    findings = [
        ("Late deliveries go together with much lower reviews",
         f"<span class='label'>Observed:</span> on-time orders average {fmt_num(on_time_review, '{:.2f}')}/5; late orders "
         f"{fmt_num(late_review, '{:.2f}')}/5, and the gap widens with each extra day late. "
         "<span class='label'>Caveat:</span> this is an association; product, seller and region also differ between late and on-time orders. "
         "<span class='label'>Next step:</span> compare like-for-like (same seller and category) or test more conservative delivery promises."),
        ("Delivery reliability drops during demand peaks",
         (f"<span class='label'>Observed:</span> the late rate peaked at {worst_month['late_pct']:.1f}% in {worst_month['year_month']} "
          f"vs {current['late_pct']:.1f}% for the selected period. "
          "<span class='label'>Hypothesis:</span> carrier and seller capacity do not scale with peak volume. "
          "<span class='label'>Next step:</span> track the late rate weekly ahead of known peaks.")
         if worst_month is not None else "No delivered orders in the selection."),
        ("Where the revenue comes from",
         f"<span class='label'>Observed:</span> the top 3 categories ({', '.join(top3['category'])}) bring "
         f"{top3['share'].sum():.0f}% of net revenue; {top_state} alone accounts for {top_state_share:.0%}. "
         "Stock-outs or delivery problems there would affect the largest share of sales."),
        ("A short list of high-volume sellers combines late deliveries and low ratings",
         f"<span class='label'>Observed:</span> {len(at_risk)} sellers with {MIN_SELLER_ORDERS}+ orders have a late rate above 10% "
         f"and an average review below 3.8, holding {m.brl(at_risk['revenue'].sum())} of revenue. "
         "<span class='label'>Next step:</span> review their fulfilment data before drawing conclusions; thresholds are a screening rule, not a verdict."),
    ]
    st.markdown("##### What the data says")
    for title, body in findings:
        st.markdown(f"<div class='insight'><h4>{title}</h4><p>{body}</p></div>", unsafe_allow_html=True)

    st.markdown("##### Suggested weekly KPI scorecard")
    st.caption("What I would put in front of an e-commerce manager every Monday. Values: selected period; trend: last month in the selection vs. the month before.")
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
        ("Freight as % of revenue", fmt_num(current["freight_pct"], "{:.1f}%"), "–", "Shipping cost pressure"),
        ("Late-delivery rate", fmt_num(current["late_pct"], "{:.1f}%"), trend(lm["late_pct"], points=True), "Early warning for review scores"),
        ("Average review score", fmt_num(current["review"], "{:.2f}"), "–", "Customer satisfaction"),
        ("Sellers to review", f"{len(at_risk)}", "–", "Account-management follow-up list"),
    ], columns=["KPI", "Value", "Last month vs. prior", "Why it matters"])
    st.dataframe(scorecard, hide_index=True, width="stretch")

    st.markdown("##### Limitations")
    st.markdown(
        "- Historical, anonymized public data (2016–2018); no costs or margins, so profitability cannot be measured.\n"
        "- Delay-vs-review results are observational associations, not causal estimates.\n"
        "- Revenue = item prices on valid orders (excludes freight and canceled/unavailable orders), in Brazilian reais (BRL).\n"
        "- Customer location = ZIP of the customer's most recent order; 268 customers have a ZIP missing from the public geolocation file ('Unknown')."
    )

# ---------------------------------------------------------------- method

with method:
    st.markdown("##### Pipeline")
    st.markdown(
        "1. **Load** — 9 raw CSV files (≈1.55M rows) into PostgreSQL `raw` tables with typed columns and PK/FK/CHECK constraints.\n"
        "2. **Clean** — `staging` layer: category translation fallbacks, one row per ZIP from 1M geolocation samples, delivery-date validity flags.\n"
        "3. **Model** — `analytics` star schema: 5 dimensions and 3 fact tables at order, item and payment grain, so multi-item / multi-payment orders never double-count revenue.\n"
        "4. **Validate** — 44 automated data-quality and reconciliation checks (keys, nulls, dates, money, cross-grain revenue totals).\n"
        "5. **Serve** — Power BI semantic model (6-page dashboard) and this web demo, both on the same definitions."
    )
    st.markdown("##### Reconciliation: this demo vs. the SQL warehouse (full dataset, no filters)")
    full = m.kpis(data["orders"])
    recon = pd.DataFrame([
        ("Net revenue", m.brl(reference["net_revenue"], 3), m.brl(full["revenue"], 3)),
        ("Valid orders", f"{reference['total_orders']:,.0f}", f"{full['orders']:,.0f}"),
        ("Average order value", f"R${reference['avg_order_value']:,.2f}", f"R${full['aov']:,.2f}"),
        ("Late-delivery rate", f"{reference['late_delivery_rate_pct']:.2f}%", f"{full['late_pct']:.2f}%"),
        ("Average review score", f"{reference['avg_review_score']:.2f}", f"{full['review']:.2f}"),
    ], columns=["KPI", "SQL (reporting.vw_executive_summary)", "This demo"])
    st.dataframe(recon, hide_index=True, width="stretch")
    st.caption("The demo reads additive pre-aggregates exported from the warehouse, so every filter combination re-aggregates "
               "to the same definitions used in SQL and Power BI (see docs/KPI_RECONCILIATION.md).")
