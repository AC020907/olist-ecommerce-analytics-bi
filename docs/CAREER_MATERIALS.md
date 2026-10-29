# Career Materials

All figures are verified against the database (see `docs/TECHNICAL_AUDIT.md`, section 1).

## GitHub repository description (≤ 350 characters)

> End-to-end e-commerce BI on public Olist data: Python + PostgreSQL pipeline, fan-out-safe star schema (5 dims, 3 facts), 44 automated data-quality checks, pytest, 6-page Power BI dashboard and a Streamlit demo reconciled to SQL.

**Topics:** `business-intelligence` `power-bi` `postgresql` `sql` `python` `data-modeling` `star-schema` `data-quality` `etl` `streamlit` `dax` `analytics-engineering`

## LinkedIn

**Featured / project description**

> **Olist E-Commerce Analytics & BI** — independent project on a public 99k-order marketplace dataset.
>
> I built the full path from raw exports to decisions: a Python pipeline that loads 1.5M rows into a layered PostgreSQL warehouse, a star schema that keeps order, item and payment grains separate so revenue is never double-counted, and 44 automated checks that reconcile revenue to the cent across every table and view. On top: a six-page Power BI dashboard and a filterable web demo.
>
> What the data showed: late orders average 2.27/5 in reviews vs 4.29/5 on time, late deliveries jumped from ~3% to 12–19% in peak months, and 41 high-volume sellers combine poor delivery with low ratings.
>
> Live app: https://olist-sales-analytics.streamlit.app
>
> Python · SQL · PostgreSQL · Power BI/DAX · pytest · Streamlit

**Post (optional)**

> A small DAX detail that changed a headline number in my BI project: `CALCULATE([Avg Review], fact[is_late] = FALSE())` also matches blank values, so ~2,900 undelivered orders were counted as "on-time". The dashboard said 4.21; SQL said 4.29. Reconciling every layer against the one below it is the most useful habit I've built. Full project and audit: [link]

## CV bullets

- Built an end-to-end BI pipeline (Python, PostgreSQL) that loads and models 1.55M rows of public Olist e-commerce data into a 5-dimension, 3-fact star schema, rebuilding idempotently in ~30 seconds — 98,207 valid orders and R$13.49M net revenue analysed across 96,096 unique customers.
- Designed 44 automated data-quality and reconciliation checks plus a 64-test pytest suite; revenue, freight and payments reconcile to the cent across order, item and payment grains, and a SQL-vs-DAX audit found and fixed two Power BI measure groups that diverged from the documented KPIs.
- Delivered a six-page Power BI dashboard and a publicly deployed Streamlit BI app (Streamlit Community Cloud, Playwright E2E tests on the live URL); analysis showed late orders average 2.27/5 vs 4.29/5 on time and identified 41 high-volume sellers combining >10% late deliveries with sub-3.8 ratings.

*Note: the previous CV wording "98,207 valid orders from 96,096 customers" mixes two populations — 96,096 is all unique customers; 94,990 have at least one valid order. Use the wording above.*


## Technical interview guide

Short answers to the questions a technical interviewer is likely to ask. Longer spoken
version: `commercial/PITCH_AND_DEMO_SCRIPTS.md`.

| Topic | What to say |
|---|---|
| **Architecture** | Four PostgreSQL schemas: `raw` (typed copies of 9 CSVs, PK/FK/CHECK), `staging` (cleaning decisions as flags), `analytics` (star schema), `reporting` (validated views). A Python CLI (`python -m olist_bi build`) rebuilds all of it in one transaction in ~30 s, so a failure never leaves a half-built model. Power BI imports `analytics`; the web demo reads parquet aggregates exported from it. |
| **Dimensional modeling** | 5 dimensions (date, customer, geography, product, seller) and 3 facts at different grains: order, order item, payment. Customer grain is `customer_unique_id` (the person), not `customer_id`, which Olist regenerates per order — otherwise the repeat rate is ~0%. |
| **Double counting** | One order can have several items and several payments. Joining items × payments row-to-row multiplies revenue. `fact_orders` pre-aggregates items, freight, payments and reviews per order; category/seller analysis uses the item fact; payment analysis uses the payment fact. A check proves fact totals equal the raw files to the cent. |
| **SQL** | CTEs, window functions (`ROW_NUMBER` for the latest address, `LAG` for MoM growth, `PERCENTILE_CONT`), `FILTER` clauses for population-specific measures, `DISTINCT ON` for the mode city/state per ZIP. |
| **Data quality** | 44 checks with error/warn severity: keys, referential integrity, nulls, dates, money, reconciliation across grains and views. Known source issues (268 ZIPs missing from geolocation, 23 impossible delivery dates) are warnings, kept visible and never silently dropped. |
| **Automation & tests** | 64 pytest tests plus Playwright E2E tests against the live app: a hand-built fixture warehouse with known answers (2-item/2-payment order, cancellations, same-day delivery, impossible dates, repeat customer who moved), idempotency, demo-vs-SQL reconciliation under date/region/state/category/seller filters, and headless Streamlit tests. GitHub Actions builds the full warehouse twice and runs everything. |
| **Dashboard** | Six Power BI pages on the star schema with a documented DAX library; a Streamlit demo for people without Power BI. Both reproduce the SQL KPIs (matrix in `docs/KPI_RECONCILIATION.md`). |
| **Results** | R$13.49M net revenue, 98,207 valid orders, AOV R$137.41; 6.77% of deliveries late; on-time orders average 4.29/5 vs 2.27/5 late; Jan–Aug 2018 revenue +138% YoY. These are findings on public data, not business outcomes I delivered. |
| **Design decisions & trade-offs** | *Late = calendar date* because the promised date has no time; the timestamp rule had flagged 1,292 on-time orders. *Pre-aggregated demo data* instead of a live DB: free hosting and exact reconciliation, at the cost of a static snapshot. *Latest address* for customer geography: simple and stable, slightly wrong for 39 customers who moved state. *Full rebuild* instead of incremental loads: right for a static 1.5M-row dataset; a growing client dataset would need incremental models. *Measures, not calculated columns*, for anything filter-dependent in DAX. |
| **What I would do next** | Incremental loads, a carrier dimension if the data had one, and causal checks (same-seller comparisons or an A/B test) before recommending logistics spend based on the review gap. |
