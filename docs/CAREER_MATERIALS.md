# Career Materials

All figures are verified against the database (see `docs/TECHNICAL_AUDIT.md`, section 1).

## GitHub repository description (≤ 350 characters)

> End-to-end e-commerce BI on public Olist data: Python + PostgreSQL pipeline, fan-out-safe star schema (5 dims, 3 facts), 42 automated data-quality checks, pytest, 6-page Power BI dashboard and a Streamlit demo reconciled to SQL.

**Topics:** `business-intelligence` `power-bi` `postgresql` `sql` `python` `data-modeling` `star-schema` `data-quality` `etl` `streamlit` `dax` `analytics-engineering`

## LinkedIn

**Featured / project description**

> **Olist E-Commerce Analytics & BI** — independent project on a public 99k-order marketplace dataset.
>
> I built the full path from raw exports to decisions: a Python pipeline that loads 1.5M rows into a layered PostgreSQL warehouse, a star schema that keeps order, item and payment grains separate so revenue is never double-counted, and 42 automated checks that reconcile revenue to the cent across every table and view. On top: a six-page Power BI dashboard and a filterable web demo.
>
> What the data showed: late orders average 2.57/5 in reviews vs 4.29/5 on time, late deliveries jumped from ~4% to 14–21% in peak months, and 44 high-volume sellers combine poor delivery with low ratings.
>
> Python · SQL · PostgreSQL · Power BI/DAX · pytest · Streamlit

**Post (optional)**

> A small DAX detail that changed a headline number in my BI project: `CALCULATE([Avg Review], fact[is_late] = FALSE())` also matches blank values, so ~2,900 undelivered orders were counted as "on-time". The dashboard said 4.21; SQL said 4.29. Reconciling every layer against the one below it is the most useful habit I've built. Full project and audit: [link]

## CV bullets

- Built an end-to-end BI pipeline (Python, PostgreSQL) that loads and models 1.55M rows of public Olist e-commerce data into a 5-dimension, 3-fact star schema, rebuilding idempotently in ~30 seconds — 98,207 valid orders and R$13.49M net revenue analysed across 96,096 unique customers.
- Designed 42 automated data-quality and reconciliation checks plus a 40-test pytest suite; revenue, freight and payments reconcile to the cent across order, item and payment grains, and a SQL-vs-DAX audit found and fixed two Power BI measure groups that diverged from the documented KPIs.
- Delivered a six-page Power BI dashboard and a Streamlit web demo; analysis showed late orders average 2.57/5 vs 4.29/5 on time and identified 44 high-volume sellers combining >10% late deliveries with sub-3.8 ratings.

*Note: the previous CV wording "98,207 valid orders from 96,096 customers" mixes two populations — 96,096 is all unique customers; 94,990 have at least one valid order. Use the wording above.*
*Before using "found and fixed" in the second bullet, apply `powerbi/measure_fixes.dax` in the .pbix and commit it; until then write "found and documented fixes for".*
