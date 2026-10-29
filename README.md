# Olist E-Commerce Analytics & BI

**A reproducible sales-analytics stack — from 1.5 million raw rows to reconciled KPIs, a Power BI executive dashboard and a client-ready web demo.**

Built on the public [Olist Brazilian e-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (99,441 orders, 2016–2018). Independent portfolio project; not commissioned by or affiliated with Olist.

![Web demo — executive overview](images/demo/01_executive_overview.png)

| Net revenue analysed | Valid orders | Unique customers | Avg order value | Late deliveries | Review: on-time vs late |
|---:|---:|---:|---:|---:|---:|
| R$ 13.49M | 98,207 | 96,096 | R$ 137.41 | 8.11% | 4.29 vs 2.57 |

Every figure above is produced by the SQL model and re-checked by the automated test suite ([data-quality report](reports/data_quality_report.md)).

---

## The business problem

An online marketplace generates data in many disconnected tables: orders, items, payments, reviews, sellers, products, locations. Answering simple management questions — *How much are we really selling? Which categories and sellers drive revenue? Where does delivery fail, and does it cost us customer satisfaction?* — requires joining them correctly. Done naively, multi-item and multi-payment orders double-count revenue, canceled orders inflate sales, and the same customer appears as thousands of "new" ones.

## The solution

1. **PostgreSQL warehouse** with `raw → staging → analytics → reporting` layers, typed columns and PK/FK/CHECK constraints.
2. **Star schema** — 5 dimensions and 3 fact tables at order, item and payment grain, so revenue is never multiplied by joins.
3. **Python pipeline** — one command rebuilds the whole warehouse in a single transaction (≈30 s), idempotently.
4. **Automated data quality** — 42 checks (keys, nulls, dates, money, cross-grain revenue reconciliation) plus 40 pytest tests on a hand-checkable fixture dataset.
5. **Power BI** — six-page executive dashboard on the star schema with a documented DAX measure library.
6. **Web demo (Streamlit)** — a guided, filterable version for clients who do not use Power BI, reconciled to the SQL KPIs.

## Key findings

- **Late delivery is strongly associated with poor reviews.** On-time orders average **4.29/5**; late ones **2.57/5**. 15+ days late, 76% of reviews are 1–2 stars.
- **Delivery breaks during demand peaks.** The late rate rose from ~3–5% in mid-2017 to **14.3%** in Nov 2017 (Black Friday) and **21.4%** in Mar 2018.
- **Revenue is geographically concentrated:** São Paulo state is **38.3%** of net revenue; the North-East has the worst delivery (Alagoas 24.0% late, avg review 3.76).
- **Seller revenue is concentrated:** the top 10% of sellers generate **67.4%** of net revenue. **44** sellers with 30+ orders combine >10% late deliveries with an average review below 3.8 — a short, actionable list.
- **Growth:** Jan–Aug 2018 net revenue was **+138.3%** vs Jan–Aug 2017; repeat customers are only **3.12%** of the base.

Details and recommendations: [business insights](insights/business_insights.md) · [recommendations](insights/recommendations.md).

## Architecture

```mermaid
flowchart LR
    A[9 Olist CSV files<br/>1.55M rows] -->|python -m olist_bi build| B[(raw<br/>typed + constrained)]
    B --> C[(staging<br/>cleaning, flags,<br/>ZIP aggregation)]
    C --> D[(analytics<br/>5 dims + 3 facts)]
    D --> E[(reporting<br/>validated views)]
    D -->|42 checks| Q[Data-quality report]
    D -->|Import| P[Power BI<br/>6-page dashboard]
    D -->|python -m olist_bi export| X[Parquet aggregates] --> S[Streamlit demo]
```

### Star schema

```mermaid
erDiagram
    dim_date ||--o{ fact_orders : order_date_key
    dim_date ||--o{ fact_order_items : order_date_key
    dim_date ||--o{ fact_payments : order_date_key
    dim_customer ||--o{ fact_orders : customer_unique_id
    dim_customer ||--o{ fact_order_items : customer_unique_id
    dim_customer ||--o{ fact_payments : customer_unique_id
    dim_geography ||--o{ dim_customer : zip_code_prefix
    dim_product ||--o{ fact_order_items : product_id
    dim_seller ||--o{ fact_order_items : seller_id
    fact_orders {
        char order_id PK
        numeric items_revenue
        numeric freight_total
        numeric payments_total
        numeric delivery_days
        bool is_late
        numeric avg_review_score
    }
    fact_order_items {
        char order_id PK
        int order_item_id PK
        numeric price
        numeric freight_value
    }
    fact_payments {
        char order_id PK
        int payment_sequential PK
        text payment_type
        numeric payment_value
    }
```

| Table | Grain | Used for |
|---|---|---|
| `fact_orders` | one order | revenue, orders, AOV, delivery, reviews (revenue pre-aggregated per order) |
| `fact_order_items` | one item in an order | category, product and seller breakdowns |
| `fact_payments` | one payment transaction | payment method and installments |
| `dim_customer` | one real person (`customer_unique_id`) | repeat behaviour, customer geography (latest address) |
| `dim_geography` | one ZIP prefix | customer region/state (seller geography comes from `dim_seller`) |

More: [star schema design](docs/star_schema_design.md) · [KPI definitions](docs/kpi_definitions.md) · [data-quality notes](docs/data_quality_notes.md).

## Metric definitions

- **Net revenue** = sum of item prices on orders not `canceled` / `unavailable` (freight excluded).
- **Orders / AOV** use the same valid-order population.
- **Late delivery** = delivered after the estimated delivery timestamp, among delivered orders with valid dates.
- **Customers** = distinct `customer_unique_id` (96,096 in the dataset; 94,990 have at least one valid order).

## Data quality and validation

`python -m olist_bi check` runs 42 checks and fails on any error-level violation. Current result on the full dataset: **38 passed, 4 warnings, 0 failed** — the warnings are known source-data characteristics (268 customers with a ZIP missing from the geolocation file, 23 deliveries recorded before carrier pickup, 9 zero-value payments, 8 valid orders without items).

Highlights:

- Gross revenue, freight and payments in the fact tables equal the raw sources **to the cent** (no fan-out).
- Net revenue reconciles across order grain, item grain and every reporting view (category, seller, geography, executive).
- `pytest` builds the warehouse from a tiny fixture dataset where every expected value is computed by hand, including a 2-item / 2-payment order, canceled and unavailable orders, impossible delivery dates and a repeat customer who moved state, and checks that a rebuild is idempotent.

An independent review of the project, including open issues, is in the [technical audit](docs/TECHNICAL_AUDIT.md).

## Reproduce it

Requirements: Python 3.11+, PostgreSQL 14+ (local install or Docker).

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # set PGHOST / PGUSER / PGPASSWORD / PGDATABASE
```

Start PostgreSQL (skip if you already have one) and create the database:

```bash
docker compose up -d db           # or: createdb olist_analytics
```

Build, validate and export:

```bash
python -m olist_bi build                                      # raw → staging → analytics → reporting (~30 s)
python -m olist_bi check --report reports/data_quality_report.md
python -m olist_bi export                                     # refreshes demo/data/*.parquet
```

Tests (integration tests need a **separate** database whose name contains `test`; they drop and rebuild schemas):

```bash
createdb olist_test
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/olist_test pytest
```

The individual SQL files still run in order with `psql` (see `sql/00_reset` … `sql/06_reporting_views`) for anyone who prefers to step through them manually.

## Web demo

```bash
streamlit run demo/app.py
```

The demo needs no database: it reads small additive aggregates (`demo/data/`, < 1 MB) exported from the warehouse, so every filter combination reproduces the SQL definitions. It has five views — executive overview, sales performance, delivery & satisfaction, insights with a suggested weekly KPI scorecard, and a reconciliation page comparing its numbers with SQL.

Deploying publicly (Streamlit Community Cloud, free): point a new app at this repository with main file `demo/app.py`; dependencies are in `demo/requirements.txt`.

| Sales performance | Delivery & satisfaction |
|---|---|
| ![Sales performance](images/demo/02_sales_performance.png) | ![Delivery and satisfaction](images/demo/03_delivery_satisfaction.png) |

## Power BI dashboard

[`powerbi/olist_business_intelligence.pbix`](powerbi/olist_business_intelligence.pbix) — Import mode on the `analytics` star schema. Pages: Executive Overview, Sales Performance, Customer Analytics, Product & Category Performance, Seller Performance, Delivery & Customer Satisfaction.

| Executive overview | Delivery & satisfaction |
|---|---|
| ![Executive overview](images/Executive_overview.png) | ![Delivery](images/Delivery_%26_Customer_Satisfaction.png) |

More pages: [sales](images/Sales_performance.png) · [customers](images/Customer_analytics.png) · [products](images/Product_%26_Category_Performance.png) · [sellers](images/Seller_performance.png). Model and connection guide: [powerbi/README.md](powerbi/README.md); measures: [dax_measures.md](powerbi/dax_measures.md).

> The current `.pbix` has older versions of a few measures (review on-time/late, freight, item revenue) than the documented library — e.g. the delivery page shows 4.22 instead of 4.29 for on-time reviews. Verified corrections are in [`powerbi/measure_fixes.dax`](powerbi/measure_fixes.dax).

## Tech stack

PostgreSQL · SQL (CTEs, window functions, constraints) · Python (psycopg, pandas, pytest) · Power BI / DAX · Streamlit / Plotly · Docker Compose · GitHub Actions

## Repository layout

```text
olist_bi/            Python pipeline: config, build, quality checks, demo export, CLI
sql/                 00_reset · 01_schema · 02_data_quality (profiling) · 03_cleaning
                     04_dimensions · 05_facts · 06_reporting_views · 07_business_queries
tests/               unit, fixture-based integration, demo-data and demo-app tests
demo/                Streamlit app + exported aggregates
powerbi/             .pbix, DAX library, measure fixes, model guide
docs/                audit, case study, schema, KPI and data-quality notes
insights/            business insights and recommendations
notebooks/           exploratory analysis (pandas)
reports/             generated data-quality report
data/raw/            the 9 original Olist CSV files
```

## Limitations

- Public, anonymized data with no costs or margins: profitability cannot be analysed.
- Delay-vs-review results are observational associations, not causal estimates.
- Sep–Dec 2016 and Sep–Oct 2018 are partial months; trend views default to Jan 2017 – Aug 2018.
- Customer geography uses each customer's most recent address.

## Author

Built by **Alejandro Cotes** — Business Intelligence & data analytics (Python, SQL, PostgreSQL, Power BI). GitHub: [@AC020907](https://github.com/AC020907).

Case study: [docs/CASE_STUDY.md](docs/CASE_STUDY.md).

## License

Code: [MIT](LICENSE). The Olist dataset is published by Olist on Kaggle under CC BY-NC-SA 4.0 (non-commercial, attribution, share-alike); it is used here only as a public sample for a portfolio project.
