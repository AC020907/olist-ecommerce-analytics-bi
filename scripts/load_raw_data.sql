-- ============================================================================
-- load_raw_data.sql
-- Loads the 9 Olist CSVs into the raw schema using \copy.
-- Run from the repository root:
--   psql -U postgres -d olist_analytics -f scripts/load_raw_data.sql
-- ============================================================================

SET client_encoding = 'UTF8';

\copy raw.customers FROM 'data/raw/olist_customers_dataset.csv' WITH (FORMAT csv, HEADER true)
\copy raw.products FROM 'data/raw/olist_products_dataset.csv' WITH (FORMAT csv, HEADER true)
\copy raw.sellers FROM 'data/raw/olist_sellers_dataset.csv' WITH (FORMAT csv, HEADER true)
\copy raw.product_category_name_translation FROM 'data/raw/product_category_name_translation.csv' WITH (FORMAT csv, HEADER true)
\copy raw.geolocation FROM 'data/raw/olist_geolocation_dataset.csv' WITH (FORMAT csv, HEADER true)
\copy raw.orders FROM 'data/raw/olist_orders_dataset.csv' WITH (FORMAT csv, HEADER true)
\copy raw.order_items FROM 'data/raw/olist_order_items_dataset.csv' WITH (FORMAT csv, HEADER true)
\copy raw.order_payments FROM 'data/raw/olist_order_payments_dataset.csv' WITH (FORMAT csv, HEADER true)
\copy raw.order_reviews FROM 'data/raw/olist_order_reviews_dataset.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')