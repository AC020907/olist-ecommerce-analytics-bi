-- ============================================================================
-- export_model_for_powerbi.sql
-- Exports the 5 dimensions + 3 fact tables to CSV for a quick-start Power
-- BI import, without requiring PostgreSQL to be reachable from the
-- machine running Power BI Desktop. Regenerate any time the underlying
-- tables change.
--
-- Run from the repository root:
--   psql -d olist_analytics -f scripts/export_model_for_powerbi.sql
--
-- The recommended path for the real, reproducible project is connecting
-- Power BI directly to PostgreSQL (native connector, Import mode) -- see
-- powerbi/README.md. This export is the fast path to start building the
-- report immediately.
-- ============================================================================

\copy (SELECT * FROM analytics.dim_date) TO 'powerbi/model_export/dim_date.csv' WITH (FORMAT csv, HEADER true)
\copy (SELECT * FROM analytics.dim_geography) TO 'powerbi/model_export/dim_geography.csv' WITH (FORMAT csv, HEADER true)
\copy (SELECT * FROM analytics.dim_customer) TO 'powerbi/model_export/dim_customer.csv' WITH (FORMAT csv, HEADER true)
\copy (SELECT * FROM analytics.dim_seller) TO 'powerbi/model_export/dim_seller.csv' WITH (FORMAT csv, HEADER true)
\copy (SELECT * FROM analytics.dim_product) TO 'powerbi/model_export/dim_product.csv' WITH (FORMAT csv, HEADER true)
\copy (SELECT * FROM analytics.fact_orders) TO 'powerbi/model_export/fact_orders.csv' WITH (FORMAT csv, HEADER true)
\copy (SELECT * FROM analytics.fact_order_items) TO 'powerbi/model_export/fact_order_items.csv' WITH (FORMAT csv, HEADER true)
\copy (SELECT * FROM analytics.fact_payments) TO 'powerbi/model_export/fact_payments.csv' WITH (FORMAT csv, HEADER true)
