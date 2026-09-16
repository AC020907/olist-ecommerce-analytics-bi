# Power BI Model & Connection Guide

The completed Power BI report is included as `olist_business_intelligence.pbix`.
It uses PostgreSQL in **Import** mode and the star-schema tables under the
`analytics` schema. The SQL reporting views remain reference/validation
outputs rather than the primary Power BI data source.

## Connection

1. Open `olist_business_intelligence.pbix` in Power BI Desktop.
2. If credentials must be reset, connect to:
   - **Server:** `localhost`
   - **Database:** `olist_analytics`
   - **Authentication:** Basic (`postgres` + your local password)
   - **Mode:** Import
3. For a local PostgreSQL instance without SSL, uncheck **Use encrypted connection**.
4. Refresh after the SQL pipeline has been rebuilt.

## Imported tables

- `analytics.dim_date`
- `analytics.dim_customer`
- `analytics.dim_geography`
- `analytics.dim_product`
- `analytics.dim_seller`
- `analytics.fact_orders`
- `analytics.fact_order_items`
- `analytics.fact_payments`

Do not import `raw.*` or `staging.*` into the semantic model. Reporting views
are useful for validation but are not required for the dashboard model.

## Active relationships

All standard relationships use **Single** cross-filter direction from the
dimension (`1`) toward the fact (`*`).

```text
dim_date[date_day]             1 -> * fact_orders[order_date_key]
dim_date[date_day]             1 -> * fact_order_items[order_date_key]
dim_date[date_day]             1 -> * fact_payments[order_date_key]

dim_customer[customer_unique_id] 1 -> * fact_orders[customer_unique_id]
dim_customer[customer_unique_id] 1 -> * fact_order_items[customer_unique_id]
dim_customer[customer_unique_id] 1 -> * fact_payments[customer_unique_id]

dim_product[product_id]       1 -> * fact_order_items[product_id]
dim_seller[seller_id]         1 -> * fact_order_items[seller_id]

dim_geography[zip_code_prefix] 1 -> * dim_customer[zip_code_prefix]
```

### Geography role

`dim_geography` is intentionally the **customer/shipping geography** dimension.
It is **not** also connected to `dim_seller`, because activating both paths
creates ambiguous filtering routes. Seller geography is analyzed directly with
`dim_seller[state]` / `dim_seller[city]`. If a future version requires a fully
conformed seller-geography dimension, create a separate role-playing dimension
(e.g. `dim_seller_geography`).

## Fact-table grain rules

- `fact_orders`: order-level KPIs, net revenue, AOV, delivery, reviews.
- `fact_order_items`: category/product/seller revenue and volume.
- `fact_payments`: payment-method and installment analysis.

Never create direct fact-to-fact relationships. One order can have multiple
items and multiple payments, so joining those facts row-to-row creates fan-out
and double counting.

## Date table

Mark `analytics dim_date[date_day]` as the model Date Table. The documented
analysis window is `2017-01-01` through `2018-08-31`; 2016 and Sep-Oct 2018 are
truncated collection edges and should not be interpreted as complete months.

## DAX

The authoritative documented formulas are in `powerbi/dax_measures.md`.
Measures are organized in a disconnected `_Measures` table. Product/category
and seller revenue measures deliberately use `fact_order_items` and exclude
`canceled` / `unavailable` orders so they reconcile with SQL reporting views.

## Dashboard pages

1. Executive Overview
2. Sales Performance
3. Customer Analytics
4. Product & Category Performance
5. Seller Performance
6. Delivery & Customer Satisfaction

Screenshots are available in `/images`.
