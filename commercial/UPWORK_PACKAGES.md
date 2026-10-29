# Upwork Packages

Prices are **proposed starting prices**, not verified Upwork market data. The market
references found (October 2026) were third-party estimates and single listings:
offshore Power BI freelancers quoted at roughly US$40–90/hour, Upwork-focused guides
at US$40–70/hour for standard dashboard work, and catalog listings for simple dashboards
from US$99–200. Because this profile starts without Upwork reviews, the packages below are
priced at an effective **US$25–35/hour** to win the first 3–5 projects, then should be raised
~30–50% once there are reviews.

| | **Basic — Sales Dashboard** | **Standard — Automated BI Reporting** | **Premium — End-to-End BI Solution** |
|---|---|---|---|
| Starting price | **US$300** | **US$750** | **US$1,800** |
| Estimated effort | 10–12 h | 25–30 h | 55–70 h |
| Data sources | 1 clean source (1–3 files/tables) | up to 3 sources | up to 5 sources incl. a database or API export |
| Dashboard pages | 2 | 4 | 6 + optional web version |
| Revisions | 2 rounds | 3 rounds | 4 rounds |
| Delivery (after data is received) | 5 days | 10 days | 3–4 weeks |

## Basic — Sales Dashboard — US$300

**For:** a small business with one reasonably clean export (e.g. a monthly sales Excel or a Shopify/WooCommerce orders CSV) that wants a clear dashboard fast.

**Scope:** Power Query cleaning inside Power BI, a simple star model, up to 10 KPI measures, 2 pages (executive overview + one breakdown: products, regions or sales reps).

**Deliverables:** .pbix file, one-page KPI definitions, reconciliation of total revenue against a figure the client provides, 20-minute walkthrough video.

**Exclusions:** merging several sources, data with heavy quality problems, publishing to Power BI Service, automated refresh.

**Dependencies:** data delivered in one go; one contact to answer questions within 2 business days.

**Why this price:** about 10–12 hours of work for a template-able deliverable; low entry price to build reviews.

**Extras:** extra page +US$90 · publish to Power BI Service and share with users +US$60 · extra revision round +US$50.

## Standard — Automated BI Reporting — US$750

**For:** a team that today copies several exports into Excel every week and wants that to stop.

**Scope:** up to 3 sources combined (e.g. orders + products + customers, or sales + targets), a transformation layer in SQL or Python so new exports are processed the same way every time, star schema, 4 pages, up to 25 measures including time intelligence (MoM, YoY, YTD), automated data-quality checks (duplicates, missing keys, revenue reconciliation).

**Deliverables:** .pbix, transformation scripts, data-quality report, KPI catalogue, refresh instructions (manual one-click or scheduled if the client has Power BI Service), 45-minute handover call.

**Exclusions:** live API integrations, more than 3 sources, row-level security, predictive analytics.

**Dependencies:** sample of every source up front; Power BI Pro licences and/or gateway provided by the client if scheduled refresh is required.

**Why this price:** ~25–30 hours; the transformation and validation layer is what removes recurring manual work, which is where most of the client's value is.

**Extras:** additional source +US$150 · row-level security (per-region/rep views) +US$150 · Streamlit web version of 2 pages +US$250.

## Premium — End-to-End BI Solution — US$1,800

**For:** a growing e-commerce or distribution business that wants a small data warehouse it owns, not just a report.

**Scope:** PostgreSQL (or the client's SQL Server/MySQL) database with raw/staging/model layers, Python pipeline with one-command rebuild, up to 5 sources, star schema with multiple fact tables, 30–40 automated data-quality and reconciliation checks, 6-page Power BI dashboard, optional browser-based version for users without Power BI, full documentation. This is the same architecture as the public Olist case study.

**Deliverables:** database scripts, pipeline code with tests, data-quality report, Power BI report, architecture and KPI documentation, Docker setup for local reproduction, 2 training sessions (manager + analyst).

**Exclusions:** cloud hosting costs, licences, enterprise data-governance programmes, machine learning.

**Dependencies:** a server or cloud database provided by the client, or agreement to run locally; access to someone who knows the business rules for returns, cancellations and discounts.

**Why this price:** ~55–70 hours; the client receives an asset that can be extended for years, and the validation layer protects every future report.

**Extras:** each additional source +US$200 · API connector (Shopify, WooCommerce, Google Sheets, etc.) from +US$250 · demand forecast page (quoted separately).

## Optional maintenance (all packages)

| Plan | Price | Includes |
|---|---|---|
| Warranty | included | 14 days of bug fixes after delivery |
| Care plan | US$150 / month | refresh and quality-check monitoring, up to 4 h of small changes |
| Hourly | US$35 / hour | new pages, new sources, larger changes (estimate first) |

## Pricing review checklist (before publishing)

- [ ] Compare with 5–10 live Upwork catalog listings for "Power BI dashboard" in your target market.
- [ ] Confirm Upwork's current service fee and adjust net income expectations.
- [ ] Raise prices after the first 3–5 five-star reviews.
