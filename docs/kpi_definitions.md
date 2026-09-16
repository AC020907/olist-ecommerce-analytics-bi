# KPI Catalog

All reference values were computed against the loaded PostgreSQL database
`olist_analytics`. Power BI imports the star schema and recomputes measures
dynamically; SQL reporting views are validation/reference answers.

## Revenue population

Primary revenue/order KPIs use **valid orders**: order status is neither
`canceled` nor `unavailable`. Gross revenue remains available only as a
secondary transparency measure.

| KPI | Reference value | Source / semantic rule |
|---|---:|---|
| Gross Revenue | R$ 13,591,643.70 | all `fact_orders.items_revenue` |
| Net Revenue | **R$ 13,494,400.74** | valid orders only |
| Total Orders | **98,207** | valid orders only |
| Total Customers | **96,096** | distinct `customer_unique_id` |
| AOV | **R$ 137.41** | Net Revenue / Total Orders |
| Net Freight | **R$ 2,241,126.29** | valid orders only |
| Freight % of Net Revenue | **16.61%** | Net Freight / Net Revenue |
| Repeat Customer Rate | **3.12%** | customer-grain attribute |
| Avg Delivery Time | ~12.6 days | valid delivery dates |
| Late Delivery Rate | ~8.11% | valid delivery dates |
| Avg Review Score | ~4.09 | order-grain review average |

## Core DAX definitions

```dax
Total Revenue =
CALCULATE(
    SUM('analytics fact_orders'[items_revenue]),
    'analytics fact_orders'[order_status] <> "canceled",
    'analytics fact_orders'[order_status] <> "unavailable"
)

Total Orders =
CALCULATE(
    COUNTROWS('analytics fact_orders'),
    'analytics fact_orders'[order_status] <> "canceled",
    'analytics fact_orders'[order_status] <> "unavailable"
)

Total Customers =
DISTINCTCOUNT('analytics fact_orders'[customer_unique_id])

AOV = DIVIDE([Total Revenue], [Total Orders])
```

## Freight

Freight and revenue must use the same valid-order population.

```dax
Total Freight =
CALCULATE(
    SUM('analytics fact_orders'[freight_total]),
    'analytics fact_orders'[order_status] <> "canceled",
    'analytics fact_orders'[order_status] <> "unavailable"
)

Freight % of Revenue = DIVIDE([Total Freight], [Total Revenue])
```

## Delivery and satisfaction

```dax
Avg Delivery Days = AVERAGE('analytics fact_orders'[delivery_days])

Late Delivery % =
DIVIDE(
    CALCULATE(COUNTROWS('analytics fact_orders'),
              'analytics fact_orders'[is_late] = TRUE()),
    CALCULATE(COUNTROWS('analytics fact_orders'),
              'analytics fact_orders'[has_valid_delivery_dates] = TRUE())
)

Avg Review Score =
AVERAGE('analytics fact_orders'[avg_review_score])

Avg Review Score On-Time =
CALCULATE(
    [Avg Review Score],
    'analytics fact_orders'[has_valid_delivery_dates] = TRUE(),
    'analytics fact_orders'[is_late] = FALSE()
)

Avg Review Score Late =
CALCULATE(
    [Avg Review Score],
    'analytics fact_orders'[has_valid_delivery_dates] = TRUE(),
    'analytics fact_orders'[is_late] = TRUE()
)
```

The explicit valid-date predicate prevents blank `is_late` rows from being
misclassified as on-time. Reference comparison: approximately **4.29 vs 2.57**.

## Customer behavior

Customer KPIs use `customer_unique_id`, never `customer_id`.

```dax
Repeat Customer Rate =
DIVIDE(
    CALCULATE(COUNTROWS('analytics dim_customer'),
              'analytics dim_customer'[is_repeat_customer] = TRUE()),
    COUNTROWS('analytics dim_customer')
)
```

## Monthly / time intelligence

The reliable full-month analysis window is **2017-01 through 2018-08**.
Do not interpret 2016 or Sep-Oct 2018 as complete demand periods.

```dax
Revenue Previous Month =
CALCULATE([Total Revenue], DATEADD('analytics dim_date'[date_day], -1, MONTH))

MoM Growth % =
DIVIDE([Total Revenue] - [Revenue Previous Month], [Revenue Previous Month])

Revenue YTD =
TOTALYTD([Total Revenue], 'analytics dim_date'[date_day])
```

For a headline comparable YoY card, use Jan-Aug 2018 against Jan-Aug 2017.
The resulting growth is approximately **138.3%**.

## Product / category performance

Category filters live on `dim_product`, which filters `fact_order_items`, not
`fact_orders`. Therefore category revenue **must not** use `[Total Revenue]`.

```dax
Item Revenue =
CALCULATE(
    SUM('analytics fact_order_items'[price]),
    'analytics fact_order_items'[order_status] <> "canceled",
    'analytics fact_order_items'[order_status] <> "unavailable"
)

Items Sold =
CALCULATE(
    COUNTROWS('analytics fact_order_items'),
    'analytics fact_order_items'[order_status] <> "canceled",
    'analytics fact_order_items'[order_status] <> "unavailable"
)
```

SQL reference: `reporting.vw_category_performance`. Top categories on the
complete valid-order population include health_beauty, watches_gifts and
bed_bath_table.

## Seller performance

Seller attributes also live at item grain, so seller revenue uses the same net
item measure:

```dax
Seller Revenue = [Item Revenue]
```

SQL reference: `reporting.vw_seller_performance`. Delivery and review metrics
are calculated from the distinct valid orders associated with each seller, so
orders with multiple items do not multiply satisfaction/delivery outcomes.

## Payments

Payment analysis stays in `fact_payments`. A single order may have multiple
payment rows, so order counts use `DISTINCTCOUNT(order_id)` when the business
question is "orders by payment method".

## Geography

`dim_geography` represents **customer/shipping geography** in the active Power
BI model. Seller geography is read directly from `dim_seller`. The SQL customer
geography view keeps unmapped ZIP prefixes in an explicit `Unknown` bucket so
its grand total reconciles to net revenue. Dashboard visuals may hide this small
bucket for presentation; headline KPIs retain it.
