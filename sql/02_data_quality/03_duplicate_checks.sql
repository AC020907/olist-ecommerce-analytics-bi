-- ============================================================================
-- 03_duplicate_checks.sql
-- Since every raw table has a PK enforced at the schema level, exact PK
-- duplicates are already impossible (the load would have failed). What's
-- worth checking instead is duplication on *business* keys that are NOT
-- the PK -- these reveal quirks in the source data itself.
-- ============================================================================

-- review_id is reused across different orders (verified: 789 review_id
-- values appear more than once, always paired with a different order_id
-- -- confirmed NOT a duplicate-row problem, since (review_id, order_id)
-- has zero duplicates and is exactly why it's the composite PK).
SELECT review_id, COUNT(*) AS times_seen, COUNT(DISTINCT order_id) AS distinct_orders
FROM raw.order_reviews
GROUP BY review_id
HAVING COUNT(*) > 1
ORDER BY times_seen DESC
LIMIT 10;

-- customer_unique_id repeats by design (a returning customer gets a new
-- customer_id per order) -- this is not a data quality defect, it's the
-- reason dim_customer must be built on customer_unique_id (Phase 5).
SELECT customer_unique_id, COUNT(*) AS order_level_ids
FROM raw.customers
GROUP BY customer_unique_id
HAVING COUNT(*) > 1
ORDER BY order_level_ids DESC
LIMIT 10;

-- Same (order_id, product_id, seller_id, price, freight_value) appearing
-- more than once is NOT a duplicate-row bug: this dataset has no
-- "quantity" column, so buying 2 units of the same product in one order
-- is represented as 2 separate order_item_id rows. Verified with a real
-- example (order 0008288aa423d2a3f00fcb17cd7d8719, order_item_id 1 and
-- 2, identical product/seller/price -- two physical units).
-- 7,088 such groups exist. This confirms the fact table grain (Phase 5):
-- SUM(price) over order_items already gives correct total revenue with
-- no need to multiply by a quantity field.
SELECT order_id, product_id, seller_id, price, freight_value, COUNT(*) AS units
FROM raw.order_items
GROUP BY order_id, product_id, seller_id, price, freight_value
HAVING COUNT(*) > 1
ORDER BY units DESC
LIMIT 10;
