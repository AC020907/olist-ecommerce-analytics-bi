# Olist E-Commerce Analytics & BI

**From 1.5 million raw marketplace rows to reconciled KPIs, a Power BI executive dashboard and an interactive web demo — with every number tested.**

*Independent portfolio project on the public [Olist Brazilian e-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (99,441 orders, 2016–2018). Not commissioned by, affiliated with, or used by Olist; no figure below is a business result I delivered to a client.*

**Demo:** `streamlit run demo/app.py` (no database needed) · public deployment steps in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

![Web demo — executive overview](images/demo/01_executive_overview.png)

| Net revenue analysed | Valid orders | Avg order value | Late deliveries | Review: on-time vs late | Data checks | Tests |
|---:|---:|---:|---:|---:|---:|---:|
| R$ 13.49M | 98,207 | R$ 137.41 | 6.77% | 4.29 vs 2.27 | 44 (0 failing) | 57 passing |

KPIs are identical in PostgreSQL, Power BI and the web demo — see the [reconciliation matrix](docs/KPI_RECONCILIATION.md).

---

## The business problem

A marketplace stores orders, items, payments, reviews, customers, sellers and products in separate tables. Answering *how much did we sell, what drives it, where does delivery fail and does it hurt satisfaction?* means joining them, and the easy joins are wrong: multi-item and multi-payment orders double-count revenue, canceled orders inflate sales, and every order looks like a new customer because Olist issues a new `customer_id` per order.

## What I built

```mermaid
flowchart LR
    A[9 Olist CSVs<br/>1.55M rows] -->|python -m olist_bi build| B[(raw<br/>typed + constrained)]
    B --> C[(staging<br/>cleaning flags)]
    C --> D[(analytics<br/>5 dims + 3 facts)]
    D --> E[(reporting<br/>validated views)]
    D -->|44 checks| Q[Data-quality report]
    D -->|Import| P[Power BI<br/>6 pages]
    D -->|export| X[Parquet aggregates] --> S[Streamlit demo]
```

- **PostgreSQL warehouse** in four layers with PK/FK/CHECK constraints, rebuilt by a **Python pipeline** in one transaction (~30 s, idempotent).
- **Star schema** with facts at order, item and payment grain, so revenue is never multiplied by joins.
- **Data quality gate:** 44 checks — keys, nulls, dates, money, and revenue reconciliation across grains and views ([report](reports/data_quality_report.md)).
- **57 automated tests**, including a hand-computed fixture warehouse and demo-vs-SQL reconciliation under date, region, state, category and seller filters; GitHub Actions builds the full warehouse twice and runs them.
- **Power BI** six-page dashboard on the star schema with a documented [DAX library](powerbi/dax_measures.md).
- **Streamlit demo** for viewers without Power BI: filters, insights with caveats, a weekly KPI scorecard and an in-app reconciliation table.

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
```

| Table | Grain | Used for |
|---|---|---|
| `fact_orders` | one order | revenue, orders, AOV, delivery, reviews (items/payments pre-aggregated per order) |
| `fact_order_items` | one item in an order | category, product and seller breakdowns |
| `fact_payments` | one payment | payment method and installments |
| `dim_customer` | one person (`customer_unique_id`) | repeat behaviour; geography of the latest order |
| `dim_geography` | one ZIP prefix | customer region/state (`Unknown` when the ZIP is missing from the public geolocation file) |

### Key definitions

- **Net revenue** = item prices on orders not `canceled`/`unavailable`, in BRL, freight excluded.
- **Late** = delivered on a later **calendar day** than promised. The promised date never has a time of day, so a delivery at 18:00 on the promised day is on time.
- **Customers** = distinct `customer_unique_id` (96,096; 94,990 with at least one valid order).

Full catalogue with numerator, denominator, population and SQL/DAX/Python implementation: [docs/KPI_RECONCILIATION.md](docs/KPI_RECONCILIATION.md).

## Findings and recommendations

Observed (associations in historical data, not causal effects):

- **Late orders are reviewed far worse:** 4.29/5 on time vs 2.27/5 late; at 8+ days late, 75–78% of reviews are 1–2 stars.
- **Late deliveries cluster in peak months:** ~3% in mid-2017, 12.4% in Nov 2017, 19.0% in Mar 2018.
- **Delivery is slower away from São Paulo:** SP 8.8 days / 4.5% late vs Alagoas 24.6 days / 21.5% late; 60% of sellers are in SP.
- **Concentration:** SP is 38.3% of revenue; the top 10% of sellers hold 67.4%; 41 sellers with 30+ orders combine >10% late deliveries and reviews below 3.8.
- **Growth:** Jan–Aug 2018 revenue +138.3% vs Jan–Aug 2017; 3.12% of customers bought more than once.

Each recommendation is written as *finding → evidence → interpretation → hypothesis → action → KPI*, and proposes the analysis or A/B test needed before acting: [insights](insights/business_insights.md) · [recommendations](insights/recommendations.md).

## Dashboards

**Web demo** (Streamlit)

| Sales performance | Delivery & satisfaction |
|---|---|
| ![Sales performance](images/demo/02_sales_performance.png) | ![Delivery and satisfaction](images/demo/03_delivery_satisfaction.png) |

**Power BI** — [`powerbi/olist_business_intelligence.pbix`](powerbi/olist_business_intelligence.pbix) (PDF export for viewers without Power BI: [`olist_business_intelligence.pdf`](powerbi/olist_business_intelligence.pdf)), Import mode on the `analytics` schema: Executive Overview, Sales, Customers, Products & Categories, Sellers, Delivery & Satisfaction.

| Executive overview | Delivery & satisfaction |
|---|---|
| ![Power BI executive overview](images/Executive_overview.png) | ![Power BI delivery](images/Delivery_%26_Customer_Satisfaction.png) |

More pages: [sales](images/Sales_performance.png) · [customers](images/Customer_analytics.png) · [products](images/Product_%26_Category_Performance.png) · [sellers](images/Seller_performance.png). Model guide: [powerbi/README.md](powerbi/README.md).

## Tech stack

PostgreSQL · SQL (CTEs, window functions, constraints) · Python (psycopg, pandas, pytest) · Power BI / DAX · Streamlit / Plotly · Docker Compose · GitHub Actions

## Repository layout

```text
olist_bi/     Python pipeline: config, build, quality checks, demo export, CLI
sql/          00_reset · 01_schema · 02_data_quality (profiling) · 03_cleaning
              04_dimensions · 05_facts · 06_reporting_views · 07_business_queries
tests/        unit, fixture integration, KPI reconciliation, demo app
demo/         Streamlit app (app.py), KPI logic (metrics.py), exported aggregates
powerbi/      .pbix, DAX library, measure change log, model guide
docs/         KPI reconciliation, technical audit, case study, deployment, design notes
insights/     findings and recommendations
notebooks/    independent pandas EDA (re-executed with the same definitions)
reports/      generated data-quality report
scripts/      Power BI source rebuild, demo screenshot capture
data/raw/     the 9 original Olist CSVs (CC BY-NC-SA 4.0)
```

## Run it

Requirements: Python 3.11+, PostgreSQL 14+ (local or Docker).

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # PGHOST / PGPORT / PGUSER / PGPASSWORD / PGDATABASE
docker compose up -d db           # or use an existing PostgreSQL and: createdb olist_analytics
```

```bash
python -m olist_bi build                                      # raw → staging → analytics → reporting
python -m olist_bi check --report reports/data_quality_report.md
python -m olist_bi export                                     # refresh demo/data/*.parquet
streamlit run demo/app.py
```

The SQL files also run in order with `psql` (`sql/00_reset` → `sql/06_reporting_views`) for step-by-step review.

## Tests and validation

```bash
createdb olist_test
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/olist_test \
OLIST_RECONCILE_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/olist_analytics pytest
```

- Integration tests need a **separate** database whose name contains `test` (they drop and rebuild schemas).
- Current results: 44 checks (40 pass, 4 documented source-data warnings, 0 failures); 57 tests passing locally (PostgreSQL 18) and in Docker (PostgreSQL 16).
- Independent review and resolution of every issue found: [docs/TECHNICAL_AUDIT.md](docs/TECHNICAL_AUDIT.md).

## Limitations

- Public, anonymized, historical data (2016–2018): no costs or margins, so no profitability analysis; no carrier field.
- Delay-vs-review results are observational; recommendations call for controlled comparisons before investment.
- Sep–Dec 2016 and Sep–Oct 2018 are partial months; trend views default to Jan 2017 – Aug 2018.
- Customer geography uses each person's latest order address.
- The demo is a static snapshot of exported aggregates, not live data.

## Data license

The data is published by Olist on Kaggle under **CC BY-NC-SA 4.0** (attribution, non-commercial, share-alike). The CSVs, the derived aggregates and the screenshots are shared under that license for education and portfolio use only; the code is [MIT](LICENSE). Details: [data/README.md](data/README.md).

## Author

**Alejandro Cotes** — Business Intelligence & analytics engineering (Python, SQL, PostgreSQL, Power BI). GitHub: [@AC020907](https://github.com/AC020907) · Case study: [docs/CASE_STUDY.md](docs/CASE_STUDY.md)
