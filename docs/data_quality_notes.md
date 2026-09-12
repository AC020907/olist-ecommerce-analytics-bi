# Data Quality Notes (Phase 1 findings)

These are the real findings from profiling the 9 raw CSV files directly
(row counts, `nunique`, null counts, orphan-key checks, and order volume
by month). They are not assumptions — every number here was measured
against the actual dataset and drives decisions made later in the SQL
and Power BI layers.

## 1. `customer_id` is not a person

`olist_customers_dataset` has 99,441 rows and 99,441 distinct
`customer_id` values, but only **96,096** distinct `customer_unique_id`
values. Olist issues a new `customer_id` every time the same person
places a new order. **2,997 real customers placed more than one order.**

**Decision:** `dim_customer` and any repeat-purchase / customer-value
analysis must key off `customer_unique_id`, never `customer_id`.

## 2. Fan-out risk between `order_items` and `order_payments`

- `order_items`: 112,650 rows for 98,666 distinct orders → 9,803 orders
  (~10%) have more than one item (avg. 1.14 items/order).
- `order_payments`: 103,886 rows for 99,440 distinct orders → 2,961
  orders (~3%) have more than one payment row (split/combined payments;
  one order has 29 payment rows).

**Decision:** never join `order_items` and `order_payments` directly at
row level — it multiplies both revenue and payment value. Each is
aggregated to `order_id` grain independently before being combined (see
`sql/05_facts`).

## 3. Delivery dates are null by design, not by error

`order_approved_at` (160 nulls), `order_delivered_carrier_date` (1,783),
`order_delivered_customer_date` (2,965) are null for orders that were
never approved/shipped/delivered. `order_status` distribution:

| status | orders |
|---|---|
| delivered | 96,478 |
| shipped | 1,107 |
| canceled | 625 |
| unavailable | 609 |
| invoiced | 314 |
| processing | 301 |
| created | 5 |
| approved | 2 |

**Decision:** delivery-time and late-delivery KPIs are computed only for
`order_status = 'delivered'`.

## 4. Usable time window: 2017-01 to 2018-08

Orders span 2016-09-04 to 2018-10-17, but monthly volume shows the
dataset is truncated at both ends: 2016 has only 329 orders total, and
Sep–Oct 2018 has only 20 orders combined, against 1,780–7,544 orders/month
in the 2017-01–2018-08 range.

**Decision:** all time-series / MoM-growth analysis excludes 2016 and
2018-09/10, and this exclusion is stated explicitly wherever a trend
chart appears — otherwise it reads as a fake collapse in sales.

## 5. Minor, low-impact issues (documented, not over-engineered)

- 610 of 32,951 products (~1.9%) have a null `product_category_name` →
  coalesced to `'unknown'` in the cleaning layer.
- `payment_type` includes 3 rows of `not_defined` — kept as-is and
  visible in the data, not silently dropped.
- `olist_geolocation_dataset` has 1,000,163 rows for a much smaller set
  of zip code prefixes, with multiple slightly different lat/lng per
  prefix and no strict key relationship to customers/sellers. It is
  aggregated (one row per zip prefix) before being used to enrich
  `dim_customer` / `dim_seller` — see `sql/04_dimensions`.

## 6. `review_id` is reused across different orders (Phase 3 finding)

789 `review_id` values appear more than once in `order_reviews`, always
paired with a *different* `order_id` each time (verified: zero duplicates
on the full row, and zero duplicates on `(review_id, order_id)`). This is
a real quirk of how Olist collected reviews, not a load error.

**Decision:** the primary key of `raw.order_reviews` is the composite
`(review_id, order_id)`, not `review_id` alone.

## 7. Repeated product lines within the same order are real units, not duplicates

7,088 groups of `(order_id, product_id, seller_id, price, freight_value)`
appear more than once in `order_items` (e.g. order
`0008288aa423d2a3f00fcb17cd7d8719` has two identical rows, `order_item_id`
1 and 2, same product/seller/price). The dataset has **no `quantity`
column** — buying 2 units of the same product is represented as 2
separate `order_item_id` rows.

**Decision:** `SUM(price)` over `order_items` already gives the correct
total revenue with no need to multiply by a quantity field. This is
confirmed, not assumed — verified with a concrete example.

## 8. Two product categories have no English translation

`portateis_cozinha_e_preparadores_de_alimentos` and `pc_gamer` exist in
`products` but have no row in `product_category_name_translation`. A
plain `LEFT JOIN` to get the English category name would silently turn
these into `NULL`.

**Decision:** the cleaning layer (Phase 4) applies `COALESCE` to fall
back to the original Portuguese name (or an explicit `'other'` bucket)
instead of losing the category.

## 9. 157 / 7 zip prefixes (customers / sellers) have no geolocation row at all

These customers/sellers will get `NULL` lat/lng after the geography
enrichment join. Documented so the staging layer handles it explicitly
(e.g. `COALESCE` to the state-level centroid, or leaving it `NULL` and
noting the gap) rather than the join silently losing rows.

## 10. Logical date-ordering anomalies in `orders`

Checked whether delivery milestones are ever chronologically impossible:

| check | violating orders |
|---|---|
| delivered before purchased | 0 |
| approved before purchased | 0 |
| shipped to carrier before approved | 1,359 (avg gap 24.8h, max ~171 days) |
| delivered to customer before shipped to carrier | 23 (up to ~16 days) |

The "shipped before approved" cases are mostly small (likely end-of-day
batch-approval timestamps logged after the fact) but include a few large
outliers. The 23 "delivered before shipped" cases are logically
impossible and are a genuine source data error.

**Decision:** delivery-time KPIs (Phase 6/7) are computed only where
`order_delivered_customer_date >= order_delivered_carrier_date`; the 23
excluded orders are documented here, not silently averaged into the
metric.

## 11. Minor value anomalies, documented not "corrected"

- 2 `order_payments` rows have `payment_installments = 0`, both
  `payment_type = 'credit_card'` — negligible volume, left as-is since
  the true value is unknown.
- 9 `order_payments` rows have `payment_value = 0` (3 `not_defined`, 6
  `voucher`) — plausible when a voucher fully covers the cost and a
  separate payment row carries the remainder.
