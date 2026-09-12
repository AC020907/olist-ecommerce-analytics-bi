-- ============================================================================
-- 01_staging_products.sql
-- Cleans product category naming (finding #8 in docs/data_quality_notes.md):
-- 610 products have a NULL category, and 2 category names that DO exist
-- have no row in the translation table. A plain LEFT JOIN would turn all
-- of these into NULL silently -- we make the fallback explicit instead.
-- ============================================================================

CREATE OR REPLACE VIEW staging.products AS
SELECT
    p.product_id,
    p.product_category_name                                  AS category_name_pt,
    COALESCE(t.product_category_name_english, p.product_category_name, 'unknown')
                                                                AS category_name_en,
    -- Explicit quality flag instead of hiding the fallback inside COALESCE.
    CASE
        WHEN p.product_category_name IS NULL THEN 'missing_category'
        WHEN t.product_category_name_english IS NULL THEN 'missing_translation'
        ELSE 'ok'
    END                                                         AS category_data_quality,
    p.product_name_lenght,
    p.product_description_lenght,
    p.product_photos_qty,
    p.product_weight_g,
    p.product_length_cm,
    p.product_height_cm,
    p.product_width_cm
FROM raw.products p
LEFT JOIN raw.product_category_name_translation t
    ON t.product_category_name = p.product_category_name;

COMMENT ON VIEW staging.products IS
'raw.products with category_name_en resolved via translation table, falling back to the Portuguese name (never NULL) when no translation exists, and to ''unknown'' when the category itself is NULL.';
