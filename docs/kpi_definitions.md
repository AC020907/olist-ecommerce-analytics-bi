# KPI Catalog (Phase 6)

Every number below was computed against the real, loaded database
(`olist_bi`) — not estimated. Re-run the SQL in `sql/06_reporting_views/`
or `sql/07_business_queries/` to reproduce any of them.

DAX measures shown here are the definitions used later in
`powerbi/dax_measures.md` (Phase 8) — repeated here so each KPI's
business definition, SQL and DAX live together, as requested.

## Why Power BI imports the star schema, not these views

These SQL views are useful as a pre-validated reference answer and for
quick exports, but the Power BI model itself imports `fact_orders`,
`fact_order_items`, `fact_payments` and the `dim_*` tables directly. A
pre-aggregated monthly-revenue view can't respond to a category slicer;
DAX measures need row-level fact data so filters from any visual
propagate correctly. The views and the DAX measures should return the
same numbers — that agreement is itself a validation check (Phase 7/8).

## Gross vs. Net revenue — a decision, not an oversight

`items_revenue` (Phase 5) is summed from every row in `order_items`,
regardless of order outcome. But 461 `canceled` orders still have item
rows recorded ($95,235.27) and 6 `unavailable` orders do too ($2,007.69)
— money billed for a sale the business did not actually complete.

**Decision:** the primary **Total Revenue** KPI is **Net Revenue**:
revenue from orders NOT in `('canceled', 'unavailable')`. Gross revenue
is kept available as a secondary figure for transparency, not hidden.

| | Value |
|---|---|
| Gross Revenue (all orders) | R$ 13,591,643.70 |
| Net Revenue (excl. canceled/unavailable) | **R$ 13,494,400.74** |
| Difference | R$ 97,242.96 |

---

## 1. Total Revenue

- **Definition:** sum of item prices for orders that represent a
  completed sale (excludes canceled/unavailable).
- **Formula:** `SUM(price) WHERE order_status NOT IN ('canceled','unavailable')`
- **SQL:** `SUM(items_revenue) FILTER (WHERE order_status NOT IN ('canceled','unavailable'))` on `fact_orders`.
- **DAX:**
  ```dax
  Total Revenue =
  CALCULATE(
      SUM(fact_orders[items_revenue]),
      fact_orders[order_status] <> "canceled",
      fact_orders[order_status] <> "unavailable"
  )
  ```
- **Real value:** **R$ 13,494,400.74**.
- **Interpretation:** this is the revenue figure that should appear on
  an executive dashboard's headline card — it reflects sales the
  business actually realized.
- **Common calculation error:** summing `price` directly from
  `order_items` without excluding canceled/unavailable orders overstates
  revenue by ~R$ 97K (0.7%) — small here, but the kind of error that
  compounds in a real production reporting error if never caught.

## 2. Total Orders

- **Definition:** count of orders considered completed sales.
- **Formula:** `COUNT(order_id) WHERE order_status NOT IN ('canceled','unavailable')`
- **SQL:** `COUNT(*) FILTER (WHERE order_status NOT IN ('canceled','unavailable'))` on `fact_orders`.
- **DAX:**
  ```dax
  Total Orders =
  CALCULATE(
      COUNTROWS(fact_orders),
      fact_orders[order_status] <> "canceled",
      fact_orders[order_status] <> "unavailable"
  )
  ```
- **Real value:** 98,207 orders (99,441 total minus 625 canceled minus 609 unavailable).
- **Common calculation error:** counting rows in `fact_order_items`
  instead of `fact_orders` — an order with 2 items would be counted
  twice.

## 3. Total Customers

- **Definition:** distinct real customers (`customer_unique_id`) who
  placed at least one order.
- **Formula:** `COUNT(DISTINCT customer_unique_id)`
- **SQL:** `COUNT(DISTINCT customer_unique_id)` on `fact_orders`, or `COUNT(*)` on `dim_customer`.
- **DAX:** `Total Customers = DISTINCTCOUNT(fact_orders[customer_unique_id])`
- **Real value:** 96,096.
- **Common calculation error:** counting `customer_id` instead of
  `customer_unique_id` gives 99,441 — wrong, because it counts the same
  returning person once per order (see data_quality_notes.md #1).

## 4. Average Order Value (AOV)

- **Definition:** average net revenue per completed order.
- **Formula:** `Total Revenue / Total Orders`
- **SQL:** `SUM(items_revenue) / COUNT(*)` on `fact_orders WHERE order_status NOT IN (...)`.
- **DAX:** `AOV = DIVIDE([Total Revenue], [Total Orders])` — a **measure**, not a calculated column, because it must recompute per filter context (by category, by month, by state).
- **Real value:** **R$ 137.41**.
- **Common calculation error:** using `AVERAGE(items_revenue)` as a
  calculated column bakes in whatever filter was active at refresh time
  and won't respond to slicers — this must be a measure using `DIVIDE`.

## 5. Average Items per Order

- **Definition:** average number of line items per order.
- **SQL:** `AVG(n_items)` on `fact_orders`.
- **DAX:** `Avg Items per Order = DIVIDE(SUM(fact_orders[n_items]), [Total Orders])`
- **Real value:** 1.13.
- **Interpretation:** confirms the Phase 1 finding — ~90% of orders have exactly one item; cross-sell is limited in this dataset.

## 6. Freight Cost / Freight % of Revenue

- **Definition:** total shipping cost, and shipping cost as a share of
  item revenue.
- **SQL:** `SUM(freight_total)`; `100 * SUM(freight_total) / SUM(items_revenue)`.
- **DAX:**
  ```dax
  Total Freight = SUM(fact_orders[freight_total])
  Freight % of Revenue = DIVIDE([Total Freight], [Total Revenue])
  ```
- **Real values:** Total Freight **R$ 2,251,909.54**; Freight is **16.57%** of gross item revenue.
- **Interpretation:** freight represents a meaningful cost layer (1 in
  every ~6 reais of item revenue) — relevant for any pricing or shipping
  subsidy discussion.

## 7. Monthly Revenue / MoM Revenue Growth

- **Definition:** net revenue trended by month, and its month-over-month
  % change, restricted to the 2017-01/2018-08 analysis window (see
  data_quality_notes.md #4).
- **SQL:** `reporting.vw_monthly_revenue` (uses `LAG()` over `year_month`).
- **DAX** (computed live from `dim_date`, not the SQL view, so it responds to any filter):
  ```dax
  Revenue Previous Month = CALCULATE([Total Revenue], DATEADD(dim_date[date_day], -1, MONTH))
  MoM Growth % = DIVIDE([Total Revenue] - [Revenue Previous Month], [Revenue Previous Month])
  ```
- **Real values (sample):** Feb 2017 +103.97% (low base month), Nov 2017
  +52.06% (Black Friday), Dec 2017 −26.07% (post Black-Friday pull-back).
- **Common calculation error:** computing MoM growth including 2016 or
  2018-09/10 produces a fake collapse at the edges — these months are
  truncated in the source data, not real demand drops.

## 8. Customer Repeat Rate

- **Definition:** share of real customers (`customer_unique_id`) with
  more than one order.
- **SQL:** `dim_customer.is_repeat_customer` (precomputed in Phase 5).
- **DAX:** `Repeat Customer Rate = DIVIDE(CALCULATE(COUNTROWS(dim_customer), dim_customer[is_repeat_customer] = TRUE), COUNTROWS(dim_customer))`
- **Real value:** **3.12%** (2,997 of 96,096 customers).
- **Interpretation:** low — expected for a multi-category marketplace
  over a ~2-year window without a loyalty program; worth stating
  explicitly rather than implying it's "bad" without that context.

## 9. Average Delivery Time / Late Delivery Rate

- **Definition:** average days from purchase to customer delivery, and
  the share of delivered orders that arrived after
  `order_estimated_delivery_date`. Computed only for orders with
  `has_valid_delivery_dates = true` (excludes the 23 orders with
  impossible date ordering — data_quality_notes.md #10).
- **SQL:** `AVG(delivery_days)`; `100 * COUNT(*) FILTER (is_late) / COUNT(*) FILTER (has_valid_delivery_dates)`.
- **DAX:**
  ```dax
  Avg Delivery Days = AVERAGE(fact_orders[delivery_days])
  Late Delivery % =
  DIVIDE(
      CALCULATE(COUNTROWS(fact_orders), fact_orders[is_late] = TRUE),
      CALCULATE(COUNTROWS(fact_orders), fact_orders[has_valid_delivery_dates] = TRUE)
  )
  ```
- **Real values:** **12.6 days** average; **8.11%** late delivery rate.
- **Common calculation error:** averaging `delivery_days` without the
  `has_valid_delivery_dates` filter would silently include `NULL`s
  correctly (AVG ignores NULL) but a naive re-implementation using
  `order_delivered_customer_date - order_purchase_timestamp` directly on
  `raw.orders` would produce negative values for the 23 anomalous rows.

## 10. Average Review Score

- **Definition:** average customer satisfaction rating (1-5), collapsed
  to one value per order before any further aggregation.
- **SQL:** `AVG(avg_review_score)` on `fact_orders`.
- **DAX:** `Avg Review Score = AVERAGE(fact_orders[avg_review_score])`
- **Real value:** **4.09 / 5**.

## 11. Orders by Payment Type

- **SQL:** `reporting.vw_payment_method_summary`.
- **DAX:** `Payment Value = SUM(fact_payments[payment_value])` sliced by `fact_payments[payment_type]`.
- **Real values:** credit_card 76,795 payments / R$ 12.54M (avg 3.51
  installments); boleto 19,784 / R$ 2.87M; voucher 5,775 / R$ 0.38M;
  debit_card 1,529 / R$ 0.22M.
- **Interpretation:** credit card dominates both volume and value, and
  is the only method used with meaningful installment plans — boleto,
  voucher and debit are effectively always paid in full (avg 1.00
  installments).

## 12. Revenue by Category / Category Performance

- **SQL:** `reporting.vw_category_performance`.
- **DAX:** `Total Revenue` sliced by `dim_product[category_name_en]`.
- **Real values (top 3):** health_beauty R$ 1,255,695.13 (4.18 avg
  review); watches_gifts R$ 1,198,185.21 (4.07); bed_bath_table R$
  1,035,964.06 (3.97).

## 13. Revenue by State / Geographic Performance

- **SQL:** `reporting.vw_customer_geography_performance`.
- **DAX:** `Total Revenue` sliced by `dim_geography[state]` / `[region]`.
- **Real values (top 3 by revenue):** SP R$ 5,163,819.56 (avg delivery
  8.8 days); RJ R$ 1,809,838.11 (15.3 days); MG R$ 1,572,334.61 (12.0
  days).
- **Interpretation:** SP is both the largest market and the fastest to
  deliver to — plausibly because most sellers are also based in SP
  (short in-state shipping distance). This is exactly the kind of
  concentration-plus-operational pattern the Phase 9 insights will dig
  into with real numbers, not a guess.

## 14. Seller Performance

- **SQL:** `reporting.vw_seller_performance`.
- **DAX:** `Total Revenue` / `Avg Delivery Days` / `Avg Review Score` sliced by `dim_seller[seller_id]`.
- **Real value (top seller):** seller `4869f7a5...` (SP): R$ 229,237.63
  revenue, 1,131 orders, 15.1 avg delivery days, 11.57% late rate, 4.13
  avg review score.
- **Interpretation:** this view is the direct input to business question
  #10 (high revenue + low satisfaction = operational risk) — answered
  with real numbers in Phase 9, not asserted here.

## Calculated columns vs. measures — the rule applied throughout

Every ratio, average or growth % above (`AOV`, `Freight % of Revenue`,
`MoM Growth %`, `Late Delivery %`, `Repeat Customer Rate`) is a **DAX
measure**, never a calculated column. A calculated column is computed
once at refresh time and stored per row — it cannot respond to a slicer
or a visual's filter context. A measure recomputes on every interaction.
The only place a calculated column would be justified in this model is a
static attribute that doesn't depend on filter context (e.g.
`dim_customer.is_repeat_customer`, which is already precomputed in SQL
at the correct grain — no need to duplicate it as a Power BI calculated
column at all).
