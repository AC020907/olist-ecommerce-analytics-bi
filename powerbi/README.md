# Power BI Model

## A note on how this phase was built

Power BI Desktop is Windows-only and isn't available in the Linux
environment used to build the SQL/PostgreSQL side of this project. This
folder therefore contains everything needed to build the `.pbix` in
Power BI Desktop yourself: the exact data model, relationships, KPI
definitions (`docs/kpi_definitions.md`), DAX measures
(`dax_measures.md`), and page-by-page design
(`docs/powerbi_dashboard_design.md`) — plus a ready-to-import CSV export
of the full star schema so you don't have to set up PostgreSQL locally
just to start building. Once you build the `.pbix`, it belongs in this
folder (`olist_dashboard.pbix`) and should be committed, unlike the CSVs.

## Two ways to connect

### Option A (recommended for the "real" pipeline story): PostgreSQL, Import mode

1. Install PostgreSQL locally (or use the same instance you used to run
   `sql/01_schema` through `sql/06_reporting_views`).
2. Reproduce the database: follow the root `README.md` → "How to
   reproduce this project".
3. In Power BI Desktop: **Get Data → PostgreSQL database** → server
   `localhost`, database `olist_bi` → **Import** mode (not DirectQuery —
   the data is small and static; Import gives full DAX performance).
4. Select the 5 `analytics.dim_*` tables and 3 `analytics.fact_*` tables
   (do not import `raw.*` or `staging.*` — those are pipeline internals).

This is the path that matches the project's real architecture
(PostgreSQL → Power BI) and is what the README documents as the
reproducible path.

### Option B (quick start): CSV import

1. Run `scripts/export_model_for_powerbi.sql` (or use the export already
   generated in `powerbi/model_export/`, gitignored because it's a
   regenerable derived artifact, not source).
2. In Power BI Desktop: **Get Data → Text/CSV**, import the 8 files in
   `powerbi/model_export/`.
3. Set data types explicitly after import — CSV import infers types and
   sometimes gets zip-prefix-like text columns wrong (none in this model,
   but always verify `zip_code_prefix` imports as Text, not a number,
   or the leading-zero issue from `docs/data_quality_notes.md` #1
   reappears in Power BI).

## Data model relationships

Set these up in Power BI's Model view (Manage Relationships), all
**single-direction** (dimension filters fact), cardinality **one-to-many**:

| From (dimension, "1" side) | To (fact, "many" side) |
|---|---|
| `dim_date[date_day]` | `fact_orders[order_date_key]` |
| `dim_date[date_day]` | `fact_order_items[order_date_key]` |
| `dim_date[date_day]` | `fact_payments[order_date_key]` |
| `dim_customer[customer_unique_id]` | `fact_orders[customer_unique_id]` |
| `dim_customer[customer_unique_id]` | `fact_order_items[customer_unique_id]` |
| `dim_customer[customer_unique_id]` | `fact_payments[customer_unique_id]` |
| `dim_product[product_id]` | `fact_order_items[product_id]` |
| `dim_seller[seller_id]` | `fact_order_items[seller_id]` |
| `dim_geography[zip_code_prefix]` | `dim_customer[zip_code_prefix]` |
| `dim_geography[zip_code_prefix]` | `dim_seller[zip_code_prefix]` |

This is technically a **snowflake extension** of the star schema:
`dim_geography` sits behind both `dim_customer` and `dim_seller` instead
of duplicating state/region logic in each. At this scale (19,015 /
96,096 / 3,095 rows) there's no meaningful performance cost, and it's
the same conformed-dimension decision documented in
`docs/star_schema_design.md`.

Three fact tables share `dim_date` and `dim_customer` — this is
intentional (a "fact constellation", not a single star): a slicer on
`dim_customer[state]` (via `dim_geography`) or on `dim_date` filters all
three facts simultaneously, which is exactly what lets a report combine
"revenue this month" (`fact_orders`) with "payment mix this month"
(`fact_payments`) correctly.

**Do not** create a relationship directly between `fact_order_items` and
`fact_payments`, or between `fact_order_items` and `dim_date` through
`fact_orders` — every fact connects to a dimension directly, never to
another fact. This is the same fan-out prevention rule from Phase 5,
now enforced at the Power BI model level, not just in SQL.

## Files in this folder

- `dax_measures.md` — the full measure library (Phase 8).
- `model_export/` — CSV export of the star schema (gitignored, regenerate
  with `scripts/export_model_for_powerbi.sql`).
- `olist_dashboard.pbix` — the Power BI file itself, built by following
  `docs/powerbi_dashboard_design.md`. Add it here once built.
