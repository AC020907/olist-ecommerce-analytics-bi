-- ============================================================================
-- 04_orphan_and_referential_checks.sql
-- FK constraints already make classic orphans (an order_items row
-- pointing to a non-existent order) impossible at the database level.
-- What's actually worth checking is referential *completeness* in the
-- other direction: keys that exist in one table but are absent from a
-- table we plan to join against for enrichment (geolocation, category
-- translation) -- these are NOT FK violations, just gaps to plan for
-- in the staging layer (Phase 4).
-- ============================================================================

-- Customer/seller zip prefixes with no matching row in geolocation at all.
-- These customers/sellers will get NULL lat/lng after the enrichment join
-- in staging -- acceptable, but must be handled (not silently dropped).
SELECT
    (SELECT COUNT(DISTINCT c.customer_zip_code_prefix)
     FROM raw.customers c
     WHERE NOT EXISTS (
         SELECT 1 FROM raw.geolocation g
         WHERE g.geolocation_zip_code_prefix = c.customer_zip_code_prefix
     )) AS customer_zip_prefixes_missing_geo,
    (SELECT COUNT(DISTINCT s.seller_zip_code_prefix)
     FROM raw.sellers s
     WHERE NOT EXISTS (
         SELECT 1 FROM raw.geolocation g
         WHERE g.geolocation_zip_code_prefix = s.seller_zip_code_prefix
     )) AS seller_zip_prefixes_missing_geo;
-- Verified: 157 customer zip prefixes and 7 seller zip prefixes have no
-- geolocation row at all.

-- product_category_name values that exist in products but have no row in
-- the translation table -- these would silently become NULL after a
-- LEFT JOIN to get the English name unless explicitly handled.
SELECT DISTINCT p.product_category_name
FROM raw.products p
WHERE p.product_category_name IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM raw.product_category_name_translation t
      WHERE t.product_category_name = p.product_category_name
  );
-- Verified: 2 categories have no translation --
-- 'portateis_cozinha_e_preparadores_de_alimentos' and 'pc_gamer'.
-- Both are handled with a fallback in staging (Phase 4), not dropped.
