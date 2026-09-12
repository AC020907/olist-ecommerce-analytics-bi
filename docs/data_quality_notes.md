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
