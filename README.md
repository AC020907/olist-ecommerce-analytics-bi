# Olist Business Intelligence — E-Commerce Analytics Platform

End-to-end Business Intelligence solution built on 98,207 real Brazilian
e-commerce orders: PostgreSQL data warehouse, advanced SQL analytics,
a fan-out-safe star schema, and a fully-specified Power BI executive
dashboard — every number in this README is a real, reproducible result,
not a projection.

**Live dashboard:** not yet published — Power BI Desktop is Windows-only
and wasn't available in the environment used to build the SQL layer of
this project (see `powerbi/README.md`). Everything needed to build the
`.pbix` in minutes — data model, relationships, DAX, page-by-page
design, and a ready CSV export of the star schema — is in this repo.

---

## Executive Summary

Using PostgreSQL, SQL, and a Power BI-ready data model, this project
turns Olist's raw transactional data into an executive reporting layer
covering revenue, customer behavior, delivery performance, and seller
risk. Three findings anchor the analysis:

- **Delivery reliability, not price or category, is the strongest lever
  on customer satisfaction found in the data**: on-time orders average
  a 4.29 review score vs. 2.57 for late ones.
- **20.9% of active sellers, representing 39.18% of seller-side
  revenue**, combine above-median revenue with below-average
  satisfaction — a concentrated, identifiable operational risk.
- **Repeat customers are only 3.12% of the base but generate 5.72% of
  revenue**, spending 87% more per head than one-time buyers.

## Business Problem

Olist's marketplace connects small Brazilian merchants to customers
nationwide, but raw transactional data (9 separate CSV tables) has no
inherent structure for answering the questions a retention, operations,
or marketplace-quality team actually needs answered: is revenue
growing, where is it concentrated, why do some orders arrive late, and
which sellers or categories put customer satisfaction at risk. This
project builds the pipeline that turns that raw data into governed,
trustworthy answers.

## Objectives

1. Model Olist's 9 raw tables into a PostgreSQL data warehouse with
   correct types, keys, and constraints (Phase 3).
2. Profile and document every real data-quality issue found, rather
   than assuming the data is clean (Phase 3-4).
3. Build a star schema that is provably safe against the fan-out /
   double-counting risk inherent in this dataset's structure (Phase 5).
4. Define a KPI catalog with business definitions, SQL, and DAX,
   computed against real data (Phase 6).
5. Design an executive Power BI dashboard (Phase 7-8).
6. Extract insights and turn them into recommendations grounded only in
   what the data actually supports (Phase 9-10).

## Dataset

[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
— 9 CSV files, ~126MB, covering orders from 2016-09-04 to 2018-10-17
(reliable monthly data: 2017-01 to 2018-08 — see
`docs/data_quality_notes.md` #4). Full source details and table grain
in `data/README.md`.

## Architecture

```
Raw Olist CSVs (9 files)
   │  scripts/load_raw_data.sql
   ▼
PostgreSQL: raw schema        (1:1 staging, correct types, PK/FK/CHECK)
   │  sql/02_data_quality      (row counts, nulls, duplicates, orphans, date logic)
   ▼
PostgreSQL: staging schema    (category fallback, geolocation aggregation,
   │                            delivery-quality flags)
   ▼
PostgreSQL: analytics schema  (star schema: 5 dims + 3 facts, fan-out-safe)
   │  sql/06_reporting_views
   ▼
PostgreSQL: reporting schema  (pre-validated views, SQL/DAX cross-check)
   │
   ▼
Power BI (Import mode, DAX measures, 6-page executive dashboard)
```

## Tech Stack

PostgreSQL 16 · SQL (CTEs, window functions, advanced joins) · Power BI
· DAX · Python/pandas (data profiling only, not the pipeline itself) ·
Git

## Database Model

**Raw layer:** 9 tables, one per source CSV, in a dedicated `raw`
schema with real primary/foreign keys and CHECK constraints — see
`sql/01_schema/`. Verified against the full dataset (not a sample):
every row loaded, zero constraint violations.

**Staging layer:** resolves specific, documented data-quality issues
(product category fallback, geolocation aggregation from 1,000,163
samples to 19,015 zip prefixes, delivery-date validity flags) — see
`sql/03_cleaning/` and `docs/data_quality_notes.md`.

**Analytics layer (star schema):** 5 dimensions (`dim_date`,
`dim_geography`, `dim_customer`, `dim_seller`, `dim_product`) and 3 fact
tables at 3 deliberately different grains (`fact_orders`,
`fact_order_items`, `fact_payments`) — full grain/key documentation and
a measured proof of the fan-out risk this design avoids in
`docs/star_schema_design.md`.

The single most important modeling decision: `customer_id` is **not** a
person (Olist issues a new one per order — 99,441 `customer_id` vs.
96,096 real `customer_unique_id`). Every customer-level metric in this
project is built on `customer_unique_id`.

## Data Pipeline

1. **Load** (`scripts/load_raw_data.sql`) — 9 CSVs into `raw.*`, verified
   row-for-row against the source.
2. **Quality checks** (`sql/02_data_quality/`) — 12 documented findings
   in `docs/data_quality_notes.md`, including a real, measured proof
   that a naive `order_items JOIN order_payments` inflates revenue by
   2.6x for orders with multiple items and payments.
3. **Cleaning** (`sql/03_cleaning/`) — category fallback, geolocation
   aggregation, delivery-date validity flags.
4. **Modeling** (`sql/04_dimensions/`, `sql/05_facts/`) — the star
   schema, with FK constraints enforced (the load would fail on any
   orphan — it didn't).
5. **Reporting** (`sql/06_reporting_views/`) — 6 pre-validated views,
   used to cross-check every DAX measure.

## SQL Analysis

`sql/07_business_queries/` answers the 10 business questions from the
project's initial scoping directly in SQL, each with the real result
documented inline as a comment — from monthly revenue trends to the
seller-level operational-risk quadrant.

## KPIs

Full catalog with business definition, formula, SQL, DAX, and
interpretation in `docs/kpi_definitions.md`. Headline figures:

| KPI | Value |
|---|---|
| Total Revenue (net) | R$ 13,494,400.74 |
| Total Orders | 98,207 |
| Total Customers | 96,096 |
| Average Order Value | R$ 137.41 |
| Freight % of Revenue | 16.57% |
| Repeat Customer Rate | 3.12% |
| Avg Delivery Time | 12.6 days |
| Late Delivery Rate | 8.11% |
| Avg Review Score | 4.09 / 5 |

## Power BI Dashboard

6 pages — Executive Overview, Sales Performance, Customer Analytics,
Product & Category Performance, Seller Performance & Operational Risk,
Delivery & Geographic Analysis — each with a defined objective, KPI
cards, specific visuals, filters, drill-down/drill-through, and the
insight it's designed to surface. Full design in
`docs/powerbi_dashboard_design.md`; DAX measure library in
`powerbi/dax_measures.md`; connection instructions and data model
relationships in `powerbi/README.md`.

## Key Insights

Full write-up with sources in `insights/business_insights.md`. Top 3:

1. On-time orders average 4.29 in review score; late orders average
   2.57 — the strongest relationship found in the data.
2. 639 of 3,053 active sellers (20.9%) combine above-median revenue
   with below-average satisfaction, representing 39.18% of seller-side
   revenue.
3. `office_furniture` is the clearest "high revenue, low satisfaction"
   category: R$273,580.70 in revenue at a 3.62 average review score
   (0.47 points below the platform average).

## Business Recommendations

Full Insight → Implication → Recommendation → Expected Impact → Metric
structure in `insights/recommendations.md`. Expected impact is stated
only where an internal benchmark supports it (e.g. the 4.29 on-time
score is a target this platform already achieves, not a guess) —
where it isn't quantifiable from this data, that's stated explicitly
rather than invented.

## Repository Structure

```text
olist-business-intelligence/
│
├── README.md
├── LICENSE
├── .gitignore
│
├── data/
│   ├── raw/                       (9 source CSVs — not committed, see data/README.md)
│   └── README.md
│
├── sql/
│   ├── 01_schema/                 (raw schema DDL: PK/FK/CHECK constraints)
│   ├── 02_data_quality/           (row counts, nulls, duplicates, orphans, date logic)
│   ├── 03_cleaning/                (staging: category fallback, geo aggregation, delivery flags)
│   ├── 04_dimensions/              (dim_date, dim_geography, dim_customer, dim_seller, dim_product)
│   ├── 05_facts/                    (fact_orders, fact_order_items, fact_payments)
│   ├── 06_reporting_views/          (6 views, cross-checked against DAX)
│   └── 07_business_queries/          (10 business questions, answered directly)
│
├── scripts/
│   ├── load_raw_data.sql
│   └── export_model_for_powerbi.sql
│
├── powerbi/
│   ├── README.md                   (connection guide + model relationships)
│   ├── dax_measures.md              (full DAX measure library)
│   ├── model_export/                 (CSV export of the star schema, gitignored/regenerable)
│   └── olist_dashboard.pbix           (add once built in Power BI Desktop)
│
├── docs/
│   ├── data_quality_notes.md
│   ├── star_schema_design.md
│   ├── kpi_definitions.md
│   └── powerbi_dashboard_design.md
│
├── insights/
│   ├── business_insights.md
│   └── recommendations.md
│
└── images/                          (dashboard screenshots, once built)
```

## How to Reproduce This Project

```bash
# 1. Get the data
#    Download the 9 CSVs from Kaggle (see data/README.md) into data/raw/

# 2. Create the database
createdb olist_bi

# 3. Build the pipeline, in order
psql -d olist_bi -f sql/01_schema/01_create_schemas.sql
psql -d olist_bi -f sql/01_schema/02_create_raw_tables.sql
psql -d olist_bi -f scripts/load_raw_data.sql
psql -d olist_bi -f sql/03_cleaning/01_staging_products.sql
psql -d olist_bi -f sql/03_cleaning/02_staging_geolocation.sql
psql -d olist_bi -f sql/03_cleaning/03_staging_orders.sql
for f in sql/04_dimensions/*.sql sql/05_facts/*.sql sql/06_reporting_views/*.sql; do
  psql -d olist_bi -f "$f"
done

# 4. (Optional) validate data quality yourself
for f in sql/02_data_quality/*.sql; do psql -d olist_bi -f "$f"; done

# 5. Export for Power BI (or connect Power BI directly to olist_bi — see powerbi/README.md)
psql -d olist_bi -f scripts/export_model_for_powerbi.sql
```

## Limitations

- **Power BI `.pbix` not included yet** — built from the complete
  design in `docs/powerbi_dashboard_design.md`, but not assembled in
  this environment (Power BI Desktop is Windows-only).
- **Time-series analysis is bounded to 2017-01/2018-08** — 2016 and the
  last two months of 2018 are truncated in the source data (329 and 20
  orders respectively, vs. 1,780+/month in the reliable window).
- **Year-over-year comparisons only work for Jan-Aug** — there's no
  reliable 2016 baseline and no Sep-Dec 2018 data.
- **Geolocation is approximate**: `dim_geography` aggregates up to
  1,000,163 raw samples per zip prefix into an average lat/lng and a
  mode city/state — precise enough for state/region analysis, not for
  point-level mapping.
- **No product-level cost data**: revenue and pricing are analyzed, but
  margin/profitability cannot be computed — this dataset has no cost of
  goods sold.
- **Expected-impact figures in `recommendations.md` are internally
  benchmarked, not causal estimates** — several recommendations
  explicitly state that the revenue/conversion impact of an action
  cannot be quantified from this data alone (e.g. seller-improvement
  program ROI depends on assumptions this dataset can't validate).

## Future Improvements

- Automate the pipeline with a scheduler (Airflow/dbt) instead of
  manually-run `.sql` scripts, with incremental loads instead of a
  one-time full load.
- Add row-level security in Power BI so a seller could see only their
  own performance page.
- Extend `dim_geography` with a proper geocoding source instead of
  averaging raw lat/lng samples.
- Build the seller risk-quadrant list (`recommendations.md` #2) into a
  recurring, automated alert rather than a one-time query.
- If cost data ever becomes available, extend the model with a margin
  fact to move from revenue-based to profitability-based KPIs.

## Author

**Alejandro Cotes**

Data Science student focused on Python, SQL, PostgreSQL, Machine
Learning, and Data Analytics.

- LinkedIn: [Add LinkedIn URL]
- GitHub: [Add GitHub URL]
