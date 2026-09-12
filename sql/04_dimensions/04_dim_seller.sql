-- ============================================================================
-- 04_dim_seller.sql
-- Grain: one row per seller_id. Unlike customers, raw.sellers has no
-- "moved address" ambiguity -- seller_id is already the natural key with
-- exactly one zip/city/state (verified: seller_id is the table's PK).
-- ============================================================================

DROP TABLE IF EXISTS analytics.dim_seller;

CREATE TABLE analytics.dim_seller AS
SELECT
    s.seller_id,
    s.seller_zip_code_prefix AS zip_code_prefix,
    s.seller_city             AS city,
    s.seller_state             AS state
FROM raw.sellers s;

ALTER TABLE analytics.dim_seller ADD PRIMARY KEY (seller_id);
CREATE INDEX ix_dim_seller_zip ON analytics.dim_seller (zip_code_prefix);

COMMENT ON TABLE analytics.dim_seller IS
'One row per seller_id. Joins to analytics.dim_geography on zip_code_prefix for region/lat/lng.';
