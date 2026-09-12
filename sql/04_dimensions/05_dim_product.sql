-- ============================================================================
-- 05_dim_product.sql
-- Grain: one row per product_id. Built directly from staging.products, so
-- the category fallback logic (Phase 4) is inherited automatically instead
-- of being duplicated here.
-- ============================================================================

DROP TABLE IF EXISTS analytics.dim_product;

CREATE TABLE analytics.dim_product AS
SELECT
    product_id,
    category_name_en,
    category_name_pt,
    category_data_quality,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm,
    product_photos_qty
FROM staging.products;

ALTER TABLE analytics.dim_product ADD PRIMARY KEY (product_id);
CREATE INDEX ix_dim_product_category ON analytics.dim_product (category_name_en);

COMMENT ON TABLE analytics.dim_product IS
'One row per product_id. category_name_en is never NULL (see staging.products fallback logic).';
