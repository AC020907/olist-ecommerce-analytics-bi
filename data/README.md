# Data

## Source

Brazilian E-Commerce Public Dataset by Olist, published on Kaggle:

https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

The dataset contains real, anonymized commercial data from Olist Store, covering
orders placed between **2016-09-04 and 2018-10-17**.

The first months of 2016 and the final months of 2018 contain limited activity.
For this reason, the main time-series analysis in this project uses the reliable
complete-month window from **2017-01 through 2018-08**.

See `docs/data_quality_notes.md` for the detailed temporal-quality assessment.

## Raw files

The 9 original CSV files are included in:

`data/raw/`

| File | Rows | Grain |
|---|---:|---|
| `olist_orders_dataset.csv` | 99,441 | 1 order |
| `olist_order_items_dataset.csv` | 112,650 | 1 item within an order |
| `olist_order_payments_dataset.csv` | 103,886 | 1 payment transaction within an order |
| `olist_order_reviews_dataset.csv` | 99,224 | 1 review of an order |
| `olist_customers_dataset.csv` | 99,441 | 1 customer_id |
| `olist_products_dataset.csv` | 32,951 | 1 product |
| `olist_sellers_dataset.csv` | 3,095 | 1 seller |
| `olist_geolocation_dataset.csv` | 1,000,163 | 1 geolocation sample per zip-code prefix |
| `product_category_name_translation.csv` | 71 | 1 category translation |

## Customer identity

`customer_id` is order-level and should not be used as the real customer identity.

Customer-level analysis in this project uses:

`customer_unique_id`

## Reproducing locally

The raw files are already included in the repository.

See the root [README](../README.md) for the full:

raw → staging → analytics → reporting → Power BI

reproduction workflow.
