# Data

## Source

Brazilian E-Commerce Public Dataset by Olist, published on Kaggle:
https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

Real, anonymized commercial data from Olist Store, covering orders placed
between **2016-09-04 and 2018-10-17** (note: 2016 and the last two months
of 2018 have very few orders — see `docs/data_quality_notes.md` for why
time-series analysis in this project uses the 2017-01 to 2018-08 window).

## Files (not committed to this repo — see `.gitignore`)

Download the 9 CSV files from Kaggle and place them in `data/raw/`:

| File | Rows | Grain |
|---|---|---|
| `olist_orders_dataset.csv` | 99,441 | 1 order |
| `olist_order_items_dataset.csv` | 112,650 | 1 item within an order |
| `olist_order_payments_dataset.csv` | 103,886 | 1 payment transaction within an order |
| `olist_order_reviews_dataset.csv` | 99,224 | 1 review of an order |
| `olist_customers_dataset.csv` | 99,441 | 1 customer_id (order-level, not person-level) |
| `olist_products_dataset.csv` | 32,951 | 1 product |
| `olist_sellers_dataset.csv` | 3,095 | 1 seller |
| `olist_geolocation_dataset.csv` | 1,000,163 | 1 lat/lng sample per zip code prefix (not unique) |
| `product_category_name_translation.csv` | 71 | 1 category (PT → EN) |

## Why raw data isn't versioned

Standard practice for a data project: raw data is either too large, licensed,
or (as here) already public elsewhere. Versioning the *pipeline* (SQL, docs,
Power BI model) instead of the data itself keeps the repo lightweight and
avoids duplicating a dataset that's one Kaggle download away.

## Reproducing locally

See the root `README.md` → "How to reproduce this project" for the full
load → clean → model sequence once the CSVs are in `data/raw/`.
