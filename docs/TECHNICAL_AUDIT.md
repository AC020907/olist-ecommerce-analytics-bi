# Technical Audit

> **Current status (branch `fix/olist-final-audit`):** see [section 6](#6-resolution-status-fixolist-final-audit).
> Sections 1–5 are the original audit and keep the figures measured at the time
> (e.g. 8.11% late under the old timestamp rule); the current figures are in
> [KPI_RECONCILIATION.md](KPI_RECONCILIATION.md).

**Scope:** full repository as of commit `323a995` (branch `main`), audited on 2026-10-29.
**Method:** every SQL layer was executed end-to-end on a fresh PostgreSQL 18 cluster
from the committed CSVs; the Power BI model (`powerbi/olist_business_intelligence.pbix`)
was opened in Power BI Desktop and its measures were read and evaluated with DAX
queries (read-only — the model was not modified). Figures below come from those runs.

Severity scale: **High** = a published number or a core workflow is wrong/broken ·
**Medium** = a definition or claim that can mislead a reader · **Low** = hygiene,
immaterial numeric effect · **Opportunity** = not a defect, an improvement.

---

## 1. Verified headline figures

| Figure (README / CV) | Verified value | Status |
|---|---:|---|
| Valid orders (excl. canceled/unavailable) | 98,207 | Confirmed (SQL and DAX) |
| Unique customers (`customer_unique_id`) | 96,096 | Confirmed — but see A-05 |
| Net revenue | R$ 13,494,400.74 | Confirmed (SQL and DAX) |
| Gross revenue | R$ 13,591,643.70 | Confirmed |
| AOV | R$ 137.41 | Confirmed |
| Freight % of net revenue | 16.61% | Confirmed in SQL; DAX shows 16.69% (A-02) |
| Late delivery rate | 8.11% | Confirmed (SQL and DAX) |
| Avg review score | 4.09 | Confirmed |
| Review on-time vs late | 4.29 vs 2.57 | SQL confirmed; **dashboard shows 4.21 vs 2.57** (A-01) |
| Repeat customer rate | 3.12% | Confirmed — definition note in A-06 |
| YoY Jan–Aug 2018 vs 2017 | +138.3% | Confirmed |
| 5 dimensions, 3 facts | — | Confirmed |

## 2. Strengths

- **Correct grain design.** Three fact tables at order, item and payment grain; revenue is
  pre-aggregated to the order in `fact_orders`. Automated checks confirm gross revenue,
  freight and payments in the facts equal the raw sources to the cent (no fan-out).
- **Customer identity handled correctly** (`customer_unique_id`, latest address), the single
  most common mistake with this dataset.
- **Typed raw layer** with PK/FK/CHECK constraints (CHAR(5) ZIPs preserve leading zeros,
  NUMERIC money).
- **Explicit data-quality decisions** (category fallback flags, impossible delivery dates
  NULLed instead of negative, `Unknown` geography bucket so totals reconcile).
- **Strong documentation**: KPI catalogue, star-schema rationale, quantified insights.

## 3. Findings

| ID | Severity | Finding | Evidence | Risk | Fix | Status |
|---|---|---|---|---|---|---|
| A-01 | **High** | Power BI measures `Avg Review Score On-Time` / `Late` do not include the `has_valid_delivery_dates` predicate documented in `docs/kpi_definitions.md` and `powerbi/dax_measures.md`. In DAX, `BLANK() = FALSE()` is true, so 2,873 orders without a valid delivery (mostly undelivered, avg review 1.76) are counted as "on-time". | DAX query on the committed .pbix: On-Time = **4.215** (all dates) / 4.218 (Jan 2017–Aug 2018); SQL = 4.29 / 4.30. Delivery page screenshot shows 4.22. | The headline finding "4.29 vs 2.57" in the README is not what the dashboard displays; a reviewer opening the .pbix sees a different number. | Corrected DAX in [`powerbi/measure_fixes.dax`](../powerbi/measure_fixes.dax). Needs to be pasted in Power BI Desktop and the file re-saved. | **Open — requires Power BI Desktop** |
| A-02 | **High** | Several .pbix measures differ from the documented net definitions: `Total Freight`, `Item Revenue`, `Seller Revenue`, `Items Sold`, `Avg Item Price` sum **all** orders, including canceled/unavailable. | `Total Freight` (DAX) = R$ 2,251,909.54 vs documented net R$ 2,241,126.29; `Item Revenue` totals gross R$ 13,591,643.70, not net. | Category and seller pages show gross figures while the docs promise net; category totals do not reconcile with the Net Revenue card (R$ 97k gap). | Same file as A-01. | **Open — requires Power BI Desktop** |
| A-03 | **High** | Pipeline not re-runnable. Second run fails: `CREATE TABLE raw.*` already exists, `\copy` appends duplicates (rejected by PK), `DROP TABLE analytics.dim_*` blocked by fact FKs and views. | Reproduced: `cannot drop table analytics.dim_date because other objects depend on it`; `duplicate key ... customers`. | Any change to the SQL requires manual cleanup; no reliable rebuild. | `sql/00_reset/00_drop_schemas.sql` + Python runner (`python -m olist_bi build`) that rebuilds all layers in a single transaction. Idempotency covered by a test. | **Fixed** |
| A-04 | Medium | No automated tests or executable quality gates. `sql/02_data_quality/` are profiling queries whose expected results live in comments. | — | Regressions in definitions would go unnoticed. | `olist_bi/quality.py` (42 checks, pass/warn/fail), 40 pytest tests incl. a hand-checkable fixture dataset, GitHub Actions workflow. | **Fixed** |
| A-05 | Medium | "98,207 valid orders **from** 96,096 customers" (CV wording) mixes populations: 96,096 counts every customer, including those whose only orders were canceled/unavailable. Customers with ≥1 valid order = **94,990**. | `vw_executive_summary.total_customers` has no status filter; DAX `Total Customers` likewise. | Small, but an interviewer who checks will find it. | Wording corrected in README, case study and CV bullets ("96,096 unique customers in the dataset"). Metric definition unchanged. | **Fixed (documentation)** |
| A-06 | Medium | Repeat-customer rate counts lifetime orders of **any** status (2,997 / 96,096 = 3.12%). Restricted to valid orders it is 2,888 / 94,990 = **3.04%**. | `dim_customer.lifetime_order_count` built from all orders. | Defensible, but undocumented. | Documented here and in KPI notes; definition unchanged to keep SQL/DAX/history consistent. | Documented |
| A-07 | Medium | "Late" compares the delivery **timestamp** with an estimated **date** at 00:00, so 1,292 orders delivered on the promised day count as late (16.5% of all late orders). Their average review is 4.04, close to on-time (4.29). | Demo delivery buckets; `is_late` in `staging.orders`. | Late rate (8.11%) is overstated vs a date-level rule (≈6.77%). | Kept as-is (changing it would move a published KPI); made visible as its own bucket ("Up to 1 day late") in the demo and documented here. | Documented |
| A-08 | Low | `Late Delivery %` denominator (`has_valid_delivery_dates`) includes 6 canceled orders that have both delivery dates; numerator only counts delivered. | 96,452 vs 96,446 in the comment of `07_business_queries/05_*.sql`. | Immaterial (<0.001 pp), SQL and DAX agree. | Documented; not changed to keep SQL = DAX. | Documented |
| A-09 | Low | `vw_payment_method_summary` includes payments of canceled orders (R$ 16.01M vs R$ 15.74M on valid orders), unlike every other reporting view. | Direct query. | Mix percentages slightly off vs the net population. | Documented. | Documented |
| A-10 | Low | 8 valid orders have no item rows (count as orders, R$ 0 revenue, lowers AOV by ~R$ 0.01). | Quality check `valid_orders_without_items`. | Immaterial. | Surfaced as a WARN check. | Monitored |
| A-11 | Low | Documentation contradiction: `sql/04_dimensions/02_dim_geography.sql` describes `dim_geography` as conformed for customers **and** sellers; Power BI docs (correctly) say customer-only. | Both files. | Reader confusion. | Clarified in README / architecture section. | Fixed (README) |
| A-12 | Low | `requirements.txt` covered only the notebook; no `.env.example`, no environment-based config, README requires 15+ manual `psql` commands. | — | Hard to reproduce. | `requirements.txt` split by purpose, `.env.example`, `docker-compose.yml`, one-command build. | Fixed |
| A-13 | Low | Executive Overview screenshot shows Word-style red spell-check underlines under the title and Net Revenue R$ 13.41M (a slicer state) next to a README that says R$ 13.49M. | `images/Executive_overview.png`. | Looks unpolished in a portfolio. | Needs a re-capture from Power BI Desktop after A-01/A-02. | **Open — manual** |
| A-14 | Opportunity | Geography uses the customer's **most recent** address for all of their orders (39 customers changed state). | `dim_customer`. | Negligible. | Documented; no change. | Documented |
| A-15 | Opportunity | ~122 MB of raw CSVs and a 27 MB .pbix live in git history. | `git count-objects`. | Slower clones; GitHub warns above 50 MB per file (none exceed it). | Optional: Git LFS or download script. Not changed (would rewrite history). | Not implemented |

No credentials, tokens or absolute paths were found in the repository. The only
connection detail (`localhost`, user `postgres`) is generic documentation.

## 4. Changes implemented on `feature/portfolio-upgrade`

- `olist_bi/` — Python package: env-based config, transactional idempotent build
  (`build`), 42 data-quality/reconciliation checks (`check`), demo pre-aggregates (`export`).
- `sql/00_reset/` — schema reset that makes rebuilds idempotent. **No business SQL was changed.**
- `tests/` — 40 tests: unit, fixture-based integration (fan-out, cancellations, impossible dates,
  repeat customers, category fallbacks, geography reconciliation, idempotency), demo-data
  reconciliation, headless Streamlit smoke tests.
- `reports/data_quality_report.md` — output of the check suite on the full dataset.
- `demo/` — Streamlit client demo reading only exported aggregates.
- `docker-compose.yml`, `.env.example`, `.github/workflows/ci.yml`, updated `requirements.txt`.
- `powerbi/measure_fixes.dax` — corrected DAX for A-01/A-02.

## 5. Verification environments

- **Native PostgreSQL 18** (Windows): full build, 42 checks and 40 tests passed.
- **Docker Compose** (`postgres:16-alpine`, the same major version as CI): `docker compose up -d db`,
  full build (15 s), 42 checks (0 failures), 40 tests passed; headline KPIs identical
  (R$ 13,494,400.74 · 98,207 orders · AOV R$ 137.41).

### Not verified

- **GitHub Actions:** the workflow has not run (nothing was pushed). Its commands are the same
  ones executed locally.
- **The notebook** was not re-executed.


## 6. Resolution status (`fix/olist-final-audit`)

| ID | Finding | Resolution | Evidence | Status |
|---|---|---|---|---|
| A-01 | On-time review measure counted blank `is_late` as on-time | DAX now uses strict `==`; saved in the `.pbix` | DAX 4.2947 = SQL on the same data; `powerbi/measure_fixes.dax` | Fixed |
| A-02 | Freight / item / seller measures included canceled orders | Valid-order filters added to 6 measures (+ `Avg Items per Order`, A-16) | DAX = SQL to the cent (`KPI_RECONCILIATION.md` §2) | Fixed |
| A-03 | Pipeline not re-runnable | `sql/00_reset` + transactional Python build | CI builds twice; `test_rebuild_is_idempotent` | Fixed |
| A-04 | No tests / quality gate | 44 checks, 57 tests, CI | `reports/data_quality_report.md`, CI runs | Fixed |
| A-05 | CV mixed customer populations | Wording corrected everywhere | `docs/CAREER_MATERIALS.md` | Fixed |
| A-06 | Repeat rate population undocumented | Documented (3.12% all statuses / 3.04% valid only) | `KPI_RECONCILIATION.md` §1 | Documented |
| A-07 | Late rule flagged same-day deliveries as late | `is_late` compares calendar dates (all promised dates are at 00:00) | checks `late_flag_uses_calendar_dates`, `promised_date_is_calendar_date`; test `test_delivery_on_promised_day_is_on_time` | **Fixed — late rate 8.11% → 6.77%, late review 2.57 → 2.27** |
| A-08 | Late-rate denominator included 6 canceled orders with dates | Denominator = `is_late IS NOT NULL` in SQL, DAX and demo | test `test_canceled_order_with_delivery_dates_is_outside_late_rate` | Fixed |
| A-09 | Payment view includes canceled orders | Kept (payment mix of all captured payments); population stated | `KPI_RECONCILIATION.md` §1 | Documented |
| A-10 | 8 valid orders without items | Monitored WARN check | quality report | Monitored |
| A-11 | `dim_geography` described as conformed for sellers | README/KPI docs state customer-only | README | Fixed |
| A-12 | Hard to reproduce | requirements, `.env.example`, Docker Compose (verified), one-command build | Section 5 | Fixed |
| A-13 | Power BI screenshot with spell-check marks and stale card | Screenshots rendered from a PDF export of the saved, refreshed report; hidden `region is not (Blank)` page filter removed (card R$ 13.41M → 13.45M); Sales/Customer subtitles state their periods | `images/*.png`, `powerbi/olist_business_intelligence.pdf` | Fixed |
| A-14 | Latest-address geography | Documented trade-off | `CAREER_MATERIALS.md` | Documented |
| A-15 | Repo weight (122 MB CSVs) | Kept for offline reproducibility; license allows redistribution with attribution | `data/README.md` | Not changed |
| A-16 | `Avg Items per Order` numerator summed all statuses (1.147 vs 1.141) | Valid-order filter in DAX | DAX = SQL 1.14 | Fixed |
| A-17 | Insight "639 sellers / 39.18%" not reproducible | Same query returns 620 / 37.34%; corrected in SQL comments and docs | `10_high_revenue_low_satisfaction.sql` | Fixed |
| A-18 | Recommendations stated causal effects ("strongest driver", "higher ROI") | Rewritten as finding → evidence → interpretation → hypothesis → action → KPI | `insights/recommendations.md` | Fixed |
| A-19 | Demo geography (state of record) differed from SQL/Power BI (ZIP-based) | Demo uses the same ZIP-based geography with `Unknown` | reconciliation tests | Fixed |

The exploratory notebook (`notebooks/`) now uses the same calendar-date rule and was re-executed;
its independent pandas results match the SQL figures (6.77% late, 4.29 vs 2.27).
