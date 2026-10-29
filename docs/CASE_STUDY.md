# Case Study — Sales Analytics & BI for a Multi-Seller E-Commerce Marketplace

*Independent portfolio project on the public Olist dataset (Brazil, 2016–2018). Olist did not commission or review this work; no results below were delivered to or measured at a real company.*

**Stack:** Python · PostgreSQL · SQL · Power BI / DAX · Streamlit · pytest · Docker Compose · GitHub Actions
**Live app:** [olist-sales-analytics.streamlit.app](https://olist-sales-analytics.streamlit.app) · **Code:** [github.com/AC020907/olist-ecommerce-analytics-bi](https://github.com/AC020907/olist-ecommerce-analytics-bi)

---

## The Challenge

A marketplace like Olist connects thousands of small sellers with customers across a country the size of a continent. Its operational data is spread across nine tables: orders, order items, payments, reviews, customers, sellers, products, category translations and one million geolocation samples.

Management questions are simple — *how much did we sell, what is growing, which sellers and categories matter, where does delivery fail, does it hurt satisfaction?* — but the data makes them easy to answer wrongly:

- An order can have several items **and** several payments. Joining them directly multiplies rows and overstates revenue.
- Canceled and unavailable orders still carry item rows worth R$ 97,243.
- The same person appears under a new `customer_id` on every order; counting those IDs makes the repeat-purchase rate look like zero.
- Some records are impossible (23 orders delivered before the carrier picked them up) and 268 customers have a ZIP code that is missing from the geolocation file.

Spreadsheets and ad-hoc queries over this kind of data produce numbers that disagree from one report to the next, and teams stop trusting them.

## The Solution

I built a small but complete BI stack that turns the raw exports into one validated source of truth, and two ways to consume it:

1. A **PostgreSQL warehouse** in four layers (`raw → staging → analytics → reporting`).
2. A **star schema** with three fact tables at different grains (order, item, payment) and five dimensions.
3. A **Python pipeline** that rebuilds everything with one command and **44 automated data-quality checks** that stop bad data from reaching a dashboard.
4. A **six-page Power BI dashboard** for analysts and managers who live in Microsoft tools.
5. A **web demo** that anyone can open in a browser, with filters, a guided narrative and a weekly KPI scorecard.

## Technical Implementation

**Ingestion.** Python (psycopg `COPY`) loads 1.55 million rows into typed tables with primary keys, foreign keys and CHECK constraints — ZIP codes stored as `CHAR(5)` to keep leading zeros, money as `NUMERIC`. The full rebuild runs in about 30 seconds in a single transaction, so a failure never leaves a half-built model.

**Cleaning (staging).** Missing and untranslated product categories get explicit fallback values *and* a quality flag; one million geolocation samples are collapsed to one row per ZIP (mode city/state, average coordinates); delivery records are flagged valid only when the dates are chronologically possible.

**Modeling (analytics).** `fact_orders` pre-aggregates items, freight, payments and reviews to one row per order, so order-level KPIs can never fan out. Product, category and seller analysis uses `fact_order_items`; payment analysis uses `fact_payments`. Customers are modeled on `customer_unique_id`, the real person.

**Validation.** Checks cover unique keys, referential integrity, required fields, date logic, monetary values and — most importantly — reconciliation: gross revenue, freight and payments equal the raw files to the cent, and net revenue is identical at order grain, item grain and in every reporting view. A pytest suite rebuilds the warehouse from a hand-built fixture dataset where every expected number is known in advance, and verifies that rebuilding twice gives the same result.

**Serving.** Power BI imports the star schema; a documented DAX library defines revenue, AOV, delivery and satisfaction measures and time intelligence. The Streamlit demo reads small exported aggregates (< 1 MB) and re-aggregates them, so its numbers match SQL exactly under any filter — a reconciliation table inside the app shows this.

**Auditing my own work.** A technical audit compared the Power BI model with SQL using DAX queries and found two measure groups in the `.pbix` that did not match the documented definitions (e.g. on-time review score 4.21 instead of 4.29, because blank delivery flags were treated as "on time"). The nine corrected measures were applied to the `.pbix`, re-verified against SQL and the report saved; a three-way reconciliation (SQL, Power BI, web demo) is in `docs/KPI_RECONCILIATION.md`. The same audit replaced a timestamp-based late rule that counted 1,292 orders delivered on the promised day as late.

## Business Insights

All figures are from the full dataset unless stated.

| Question | Answer |
|---|---|
| How much was sold? | R$ 13.49M net revenue over 98,207 valid orders; AOV R$ 137.41 |
| Is it growing? | Jan–Aug 2018 revenue +138.3% vs Jan–Aug 2017; peak month Nov 2017 (R$ 1.00M, Black Friday) |
| Where does revenue come from? | São Paulo state = 38.3% of revenue; top 3 of 74 categories = 25.9% |
| Who sells it? | Top 10% of 3,053 active sellers = 67.4% of revenue |
| How reliable is delivery? | 12.6 days on average; 6.77% late overall (delivered after the promised day), 12.4% in Nov 2017 and 19.0% in Mar 2018 |
| Does delivery affect satisfaction? | On-time orders average 4.29/5, late orders 2.27/5; at 8+ days late, 75–78% of reviews are 1–2 stars (association, not proven cause) |
| Where is the risk concentrated? | North-East states (Alagoas 21.5% late, review 3.76); 41 sellers with 30+ orders combine >10% late and <3.8 average review |
| Do customers come back? | 3.12% of customers placed more than one order |

## Business Value

What a company would gain from a solution like this — **potential value, not measured results**, since this is a public-data case study:

- **One trusted revenue number.** Finance, sales and operations read the same reconciled definition instead of arguing over spreadsheets.
- **Early warning on customer experience.** The late-delivery rate moves weeks before review scores and repeat purchases do; monitoring it weekly by region and seller would let operations react during peak season rather than after it.
- **A short, actionable seller list.** Instead of reviewing 3,000 sellers, account managers can start with the 41 high-volume sellers whose delivery and ratings are both poor.
- **Faster reporting.** Rebuilding and validating the model takes one command instead of a manual monthly process.
- **Safer change.** Automated checks catch broken joins or definition drift before a wrong number reaches an executive.

What was **demonstrated**: correct, reconciled metrics; reproducible processing; and analyses that answer the questions above. What was **not**: any revenue, cost or satisfaction improvement — that would require deployment at a real business.

## Deliverables

| Deliverable | Where |
|---|---|
| Data pipeline (Python + SQL, idempotent, one command) | `olist_bi/`, `sql/` |
| Data warehouse (PostgreSQL star schema, 4 layers) | `sql/01_schema` … `sql/06_reporting_views` |
| Validated business metrics (KPI catalogue + 44 checks) | `docs/kpi_definitions.md`, `reports/data_quality_report.md` |
| Executive dashboard (Power BI, 6 pages) | `powerbi/` |
| Web demo with weekly KPI scorecard | `demo/` |
| Documentation (architecture, audit, insights) | `README.md`, `docs/`, `insights/` |
| Reproducible workflow (tests, Docker Compose, CI) | `tests/`, `docker-compose.yml`, `.github/workflows/` |

## Limitations

- Case study on a **public, anonymized dataset**; not an implementation contracted by Olist or any client.
- No cost or margin data, so profitability is out of scope.
- The delay–satisfaction relationship is an observed association, not a causal estimate.
- "Late" compares the delivery timestamp with the promised date; 1,292 orders delivered on the promised day count as late under this rule.
- Data ends in 2018; partial months at both edges are excluded from trend views by default.
