-- ============================================================================
-- 02_null_checks.sql
-- Counts nulls in every column where NULL is structurally possible.
-- Columns not listed here are NOT NULL at the schema level, so a null
-- there would have made the load itself fail -- no need to re-check.
-- ============================================================================

-- orders: nulls are expected for orders that never progressed past a
-- certain status (see order_status distribution in 05_value_and_date_range_checks.sql)
SELECT
    COUNT(*)                                                AS total_orders,
    COUNT(*) FILTER (WHERE order_approved_at IS NULL)        AS null_approved_at,
    COUNT(*) FILTER (WHERE order_delivered_carrier_date IS NULL)  AS null_delivered_carrier,
    COUNT(*) FILTER (WHERE order_delivered_customer_date IS NULL) AS null_delivered_customer
FROM raw.orders;
-- Expected: 160 / 1,783 / 2,965 (verified in Phase 1 against the CSV).

-- products: category and the three "descriptive" attributes are null
-- together for the same 610 rows (products with essentially no listing
-- data), while weight/dimensions are null for a separate, much smaller
-- set of 2 rows.
SELECT
    COUNT(*)                                                    AS total_products,
    COUNT(*) FILTER (WHERE product_category_name IS NULL)        AS null_category,
    COUNT(*) FILTER (WHERE product_name_lenght IS NULL)           AS null_name_length,
    COUNT(*) FILTER (WHERE product_description_lenght IS NULL)     AS null_description_length,
    COUNT(*) FILTER (WHERE product_photos_qty IS NULL)              AS null_photos_qty,
    COUNT(*) FILTER (WHERE product_weight_g IS NULL)                 AS null_weight,
    COUNT(*) FILTER (WHERE product_length_cm IS NULL)                 AS null_length_cm
FROM raw.products;
-- Expected: 610 nulls for category/name/description/photos (same rows),
-- 2 separate nulls for weight/length/height/width.

-- order_reviews: free-text fields are optional by nature (a star rating
-- with no comment is a normal, common case, not a data quality issue).
SELECT
    COUNT(*)                                                     AS total_reviews,
    COUNT(*) FILTER (WHERE review_comment_title IS NULL)          AS null_title,
    COUNT(*) FILTER (WHERE review_comment_message IS NULL)         AS null_message
FROM raw.order_reviews;
