# DAX Measure Library (Phase 8)

All measures assume the model relationships from `powerbi/README.md`.
Create a dedicated disconnected table named `_Measures` (Enter Data →
one dummy column) to hold all of these — a common Power BI practice
that keeps measures out of the physical fact/dim tables in the field
list, purely organizational, no effect on calculation.

Every value cited here was verified against the live database in
`docs/kpi_definitions.md`; this file focuses on the DAX itself and on
**why each one is a measure and not a calculated column**.

## Calculated column vs. measure — the rule, applied consistently

A **calculated column** is evaluated once per row at data-refresh time
and stored physically in the table. It cannot react to a slicer, a
visual's filter context, or cross-filtering from another visual. A
**measure** is evaluated on demand, inside whatever filter context is
currently active.

**Rule applied throughout this project:** every ratio, average, growth
rate, or anything meant to respond to a slicer is a measure. The ONLY
calculated column in this model is `Revenue Bucket` on `fact_orders`
(below) — a static bucket label that, by definition, should NOT change
based on what's currently filtered; it is a one-time classification of
each order, exactly the case calculated columns exist for.

```dax
Revenue Bucket =
SWITCH(
    TRUE(),
    fact_orders[items_revenue] < 50,  "1. < R$50",
    fact_orders[items_revenue] < 100, "2. R$50-100",
    fact_orders[items_revenue] < 150, "3. R$100-150",
    fact_orders[items_revenue] < 250, "4. R$150-250",
    fact_orders[items_revenue] < 500, "5. R$250-500",
    "6. R$500+"
)
```

Everything else below is a measure.

---

## Base additive measures

```dax
Total Revenue =
CALCULATE(
    SUM(fact_orders[items_revenue]),
    fact_orders[order_status] <> "canceled",
    fact_orders[order_status] <> "unavailable"
)
```
Real value (no filter): R$ 13,494,400.74. See `docs/kpi_definitions.md`
for the gross-vs-net revenue decision this encodes.

```dax
Gross Revenue = SUM(fact_orders[items_revenue])
```
Kept as a secondary, transparent measure — not the headline KPI.

```dax
Total Orders =
CALCULATE(
    COUNTROWS(fact_orders),
    fact_orders[order_status] <> "canceled",
    fact_orders[order_status] <> "unavailable"
)
```

```dax
Total Customers = DISTINCTCOUNT(fact_orders[customer_unique_id])
```
Using `fact_orders` (not `dim_customer`) so this measure respects
whatever filter context is active (e.g. "customers who ordered in
region X this month") rather than always returning the full 96,096.

```dax
Total Freight = SUM(fact_orders[freight_total])
Total Payment Value = SUM(fact_payments[payment_value])
```

## Ratio measures — always with DIVIDE, never a bare `/`

`DIVIDE(numerator, denominator, [alternate result])` returns `BLANK()`
(or the alternate result) on a zero denominator instead of throwing a
division error — essential once a slicer can filter a group down to
zero rows.

```dax
AOV = DIVIDE([Total Revenue], [Total Orders])
```
Real value: R$ 137.41.

```dax
Freight % of Revenue = DIVIDE([Total Freight], [Total Revenue])
```
Real value: 16.57%. Format as percentage in Power BI, not multiplied by
100 in the DAX itself.

```dax
Avg Items per Order = DIVIDE(SUM(fact_orders[n_items]), [Total Orders])
```
Real value: 1.13.

```dax
Avg Delivery Days = AVERAGE(fact_orders[delivery_days])
```
Real value: 12.6. `AVERAGE` already ignores `BLANK()`, which is exactly
what `delivery_days` is for non-delivered orders and the 23 orders with
impossible date ordering (Phase 4/5) — no extra filter needed here.

```dax
Late Delivery % =
DIVIDE(
    CALCULATE(COUNTROWS(fact_orders), fact_orders[is_late] = TRUE),
    CALCULATE(COUNTROWS(fact_orders), fact_orders[has_valid_delivery_dates] = TRUE)
)
```
Real value: 8.11%. The denominator is deliberately
`has_valid_delivery_dates = TRUE`, not `COUNTROWS(fact_orders)` — using
total orders as the denominator would silently understate the rate by
diluting it with orders that were never delivered at all.

```dax
Avg Review Score = AVERAGE(fact_orders[avg_review_score])
```
Real value: 4.09.

```dax
Repeat Customer Rate =
DIVIDE(
    CALCULATE(COUNTROWS(dim_customer), dim_customer[is_repeat_customer] = TRUE),
    COUNTROWS(dim_customer)
)
```
Real value: 3.12%. Built on `dim_customer`, not `fact_orders` — repeat
status is a customer attribute (Phase 5), and computing it from
`fact_orders` would require a separate `DISTINCTCOUNT` + join logic
this measure avoids entirely by relying on the SQL layer having already
gotten it right.

## Time intelligence

These require `dim_date[date_day]` marked as the model's **Date Table**
(Model view → right-click `dim_date` → Mark as Date Table) for
`DATEADD`/`TOTALYTD` to work correctly.

```dax
Revenue Previous Month =
CALCULATE([Total Revenue], DATEADD(dim_date[date_day], -1, MONTH))
```

```dax
MoM Growth % = DIVIDE([Total Revenue] - [Revenue Previous Month], [Revenue Previous Month])
```
Real example: Aug 2018 revenue R$848,860.10 vs. Jul 2018
R$878,044.27 → **−3.32%**, matching `reporting.vw_monthly_revenue`
exactly (the SQL/DAX agreement check from `docs/kpi_definitions.md`).

```dax
Revenue YTD = TOTALYTD([Total Revenue], dim_date[date_day])
```
Real value at Aug 2018: **R$ 7,341,037.41**.

```dax
Revenue Previous Year = CALCULATE([Total Revenue], DATEADD(dim_date[date_day], -1, YEAR))

YoY Growth % = DIVIDE([Total Revenue] - [Revenue Previous Year], [Revenue Previous Year])
```

**Documented limitation, not a silent gap:** the dataset only has
reliable monthly data from 2017-01 to 2018-08 (`data_quality_notes.md`
#4). `Revenue Previous Year` is only meaningful for 2018 dates (compared
against the equivalent 2017 month, which exists); for a 2017 date it
would compare against 2016, which has only 329 orders total and is not
a real basis for comparison. **The only valid YoY comparison in this
dataset is Jan-Aug 2018 vs. Jan-Aug 2017:**

| Period | Revenue |
|---|---|
| Jan-Aug 2017 | R$ 3,080,850.81 |
| Jan-Aug 2018 | R$ 7,341,037.41 |
| YoY Growth | **+138.31%** |

The dashboard should either restrict any YoY visual to this window
explicitly, or add a visible note next to it — showing YoY for 2017
dates without that caveat would silently compare against a
near-empty 2016.

## Share / ranking measures

```dax
Revenue Share % =
DIVIDE(
    [Total Revenue],
    CALCULATE([Total Revenue], ALL(dim_product[category_name_en]))
)
```
Generic pattern: use `ALL()` on whatever dimension column the current
visual is broken down by (category here; swap for `dim_geography[state]`
on the geography page, `dim_seller[seller_id]` on the seller page,
etc. — one measure per breakdown, since `ALL()` needs a specific column).

```dax
Category Revenue Rank = RANKX(ALL(dim_product[category_name_en]), [Total Revenue])
```

## Segment-comparison measures (Customer Analytics page)

```dax
Avg Revenue per Repeat Customer =
CALCULATE(
    DIVIDE([Total Revenue], DISTINCTCOUNT(fact_orders[customer_unique_id])),
    dim_customer[is_repeat_customer] = TRUE
)

Avg Revenue per New Customer =
CALCULATE(
    DIVIDE([Total Revenue], DISTINCTCOUNT(fact_orders[customer_unique_id])),
    dim_customer[is_repeat_customer] = FALSE
)
```
Real values: R$ 258.40 (repeat) vs. R$ 138.28 (new) — the headline
comparison on Page 3.

## On-time vs. late satisfaction comparison (Page 6's key measure)

```dax
Avg Review Score On-Time =
CALCULATE([Avg Review Score], fact_orders[is_late] = FALSE)

Avg Review Score Late =
CALCULATE([Avg Review Score], fact_orders[is_late] = TRUE)
```
Real values: **4.29** vs. **2.57** — verified against the live database,
the single strongest relationship in the whole project.
