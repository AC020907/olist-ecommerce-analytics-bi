# DAX Measure Library

This file documents the semantic-layer calculations used by the Power BI
report. Table names match the imported model. All measures should live in a
disconnected `_Measures` table unless otherwise stated.

## Static calculated column

Create in `analytics fact_orders`:

```dax
Revenue Bucket =
SWITCH(
    TRUE(),
    'analytics fact_orders'[items_revenue] < 50,  "1. < R$50",
    'analytics fact_orders'[items_revenue] < 100, "2. R$50-100",
    'analytics fact_orders'[items_revenue] < 150, "3. R$100-150",
    'analytics fact_orders'[items_revenue] < 250, "4. R$150-250",
    'analytics fact_orders'[items_revenue] < 500, "5. R$250-500",
    "6. R$500+"
)
```

Everything below is a **measure**.

## Revenue and orders

```dax
Total Revenue =
CALCULATE(
    SUM('analytics fact_orders'[items_revenue]),
    'analytics fact_orders'[order_status] <> "canceled",
    'analytics fact_orders'[order_status] <> "unavailable"
)

Gross Revenue =
SUM('analytics fact_orders'[items_revenue])

Total Orders =
CALCULATE(
    COUNTROWS('analytics fact_orders'),
    'analytics fact_orders'[order_status] <> "canceled",
    'analytics fact_orders'[order_status] <> "unavailable"
)

Total Customers =
DISTINCTCOUNT('analytics fact_orders'[customer_unique_id])

AOV =
DIVIDE([Total Revenue], [Total Orders])
```

## Freight

Use net freight with net revenue so numerator and denominator represent the
same valid-order population.

```dax
Total Freight =
CALCULATE(
    SUM('analytics fact_orders'[freight_total]),
    'analytics fact_orders'[order_status] <> "canceled",
    'analytics fact_orders'[order_status] <> "unavailable"
)

Freight % of Revenue =
DIVIDE([Total Freight], [Total Revenue])
```

Reference result on the complete dataset: approximately **16.61%**.

## Order behavior

```dax
Avg Items per Order =
DIVIDE(
    CALCULATE(
        SUM('analytics fact_orders'[n_items]),
        'analytics fact_orders'[order_status] <> "canceled",
        'analytics fact_orders'[order_status] <> "unavailable"
    ),
    [Total Orders]
)
```

## Delivery and satisfaction

```dax
Avg Delivery Days =
AVERAGE('analytics fact_orders'[delivery_days])

Late Delivery % =
DIVIDE(
    CALCULATE(
        COUNTROWS('analytics fact_orders'),
        'analytics fact_orders'[is_late] = TRUE()
    ),
    CALCULATE(
        COUNTROWS('analytics fact_orders'),
        'analytics fact_orders'[has_valid_delivery_dates] = TRUE()
    )
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

The explicit valid-date filter on the on-time measure is important. Orders with
`is_late = BLANK()` must not be silently treated as on-time. SQL/notebook
reference values are approximately **4.29 on-time vs 2.57 late**.

## Customer measures

```dax
Repeat Customer Rate =
DIVIDE(
    CALCULATE(
        COUNTROWS('analytics dim_customer'),
        'analytics dim_customer'[is_repeat_customer] = TRUE()
    ),
    COUNTROWS('analytics dim_customer')
)

Avg Revenue per Repeat Customer =
CALCULATE(
    DIVIDE(
        [Total Revenue],
        DISTINCTCOUNT('analytics fact_orders'[customer_unique_id])
    ),
    'analytics dim_customer'[is_repeat_customer] = TRUE()
)

Avg Revenue per New Customer =
CALCULATE(
    DIVIDE(
        [Total Revenue],
        DISTINCTCOUNT('analytics fact_orders'[customer_unique_id])
    ),
    'analytics dim_customer'[is_repeat_customer] = FALSE()
)
```

## Time intelligence

Mark `analytics dim_date[date_day]` as the Date Table first.

```dax
Revenue Previous Month =
CALCULATE(
    [Total Revenue],
    DATEADD('analytics dim_date'[date_day], -1, MONTH)
)

MoM Growth % =
DIVIDE(
    [Total Revenue] - [Revenue Previous Month],
    [Revenue Previous Month]
)

Revenue YTD =
TOTALYTD(
    [Total Revenue],
    'analytics dim_date'[date_day]
)

Revenue Previous Year =
CALCULATE(
    [Total Revenue],
    DATEADD('analytics dim_date'[date_day], -1, YEAR)
)

YoY Growth % =
DIVIDE(
    [Total Revenue] - [Revenue Previous Year],
    [Revenue Previous Year]
)

YoY Comparable Period % =
VAR Revenue2018 =
    CALCULATE(
        [Total Revenue],
        DATESBETWEEN(
            'analytics dim_date'[date_day],
            DATE(2018, 1, 1),
            DATE(2018, 8, 31)
        )
    )
VAR Revenue2017 =
    CALCULATE(
        [Total Revenue],
        DATESBETWEEN(
            'analytics dim_date'[date_day],
            DATE(2017, 1, 1),
            DATE(2017, 8, 31)
        )
    )
RETURN
DIVIDE(Revenue2018 - Revenue2017, Revenue2017)
```

`YoY Comparable Period %` is the headline comparable-period card. The standard
`YoY Growth %` remains useful in a month-level visual restricted to Jan-Aug
2018.

## Product/category measures

Product/category analysis must use `fact_order_items`; `dim_product` does not
filter `fact_orders` directly. Exclude canceled/unavailable orders so DAX
reconciles with `reporting.vw_category_performance`.

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

Avg Item Price =
CALCULATE(
    AVERAGE('analytics fact_order_items'[price]),
    'analytics fact_order_items'[order_status] <> "canceled",
    'analytics fact_order_items'[order_status] <> "unavailable"
)

Category Revenue Share % =
DIVIDE(
    [Item Revenue],
    CALCULATE(
        [Item Revenue],
        ALL('analytics dim_product'[category_name_en])
    )
)

Category Revenue Rank =
IF(
    ISINSCOPE('analytics dim_product'[category_name_en]),
    RANKX(
        ALL('analytics dim_product'[category_name_en]),
        [Item Revenue],
        ,
        DESC
    ),
    BLANK()
)
```

## Seller measures

Seller revenue is item-grain revenue and must use the same valid-order
definition as category revenue.

```dax
Seller Revenue =
[Item Revenue]

Seller Revenue Rank =
IF(
    ISINSCOPE('analytics dim_seller'[seller_id]),
    RANKX(
        ALL('analytics dim_seller'[seller_id]),
        [Seller Revenue],
        ,
        DESC
    ),
    BLANK()
)
```

## Payment measures

Payment analysis stays on `fact_payments` and never joins row-level to item
facts.

```dax
Total Payment Value =
SUM('analytics fact_payments'[payment_value])

Payment Orders =
DISTINCTCOUNT('analytics fact_payments'[order_id])

Payment Share % =
DIVIDE(
    [Total Payment Value],
    CALCULATE(
        [Total Payment Value],
        ALL('analytics fact_payments'[payment_type])
    )
)
```

## Geography share measures

The active geography role is customer geography.

```dax
Geography Revenue Share % =
DIVIDE(
    [Total Revenue],
    CALCULATE(
        [Total Revenue],
        ALL('analytics dim_geography'[state])
    )
)

Region Revenue Share % =
DIVIDE(
    [Total Revenue],
    CALCULATE(
        [Total Revenue],
        ALL('analytics dim_geography'[region])
    )
)
```

## Validation references

Use SQL reporting views as reference answers. Important full-dataset checks:

- Net Revenue: **R$ 13,494,400.74**
- Total Orders (valid): **98,207**
- Total Customers: **96,096**
- AOV: **R$ 137.41**
- Avg Review Score: **4.09**
- Late Delivery Rate: **~8.11%**
- Repeat Customer Rate: **3.12%**
- Avg Review Score On-Time: **~4.29**
- Avg Review Score Late: **~2.57**
- Revenue YTD at Aug-2018: **R$ 7,341,037.41**
- Jan-Aug 2018 vs Jan-Aug 2017 comparable YoY: **~138.3%**

Dashboard pages may use the 2017-01 through 2018-08 analysis window, so card
values can differ slightly from full-dataset reference values.
