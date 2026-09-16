# Olist Business Intelligence — E-Commerce Analytics Platform

End-to-end Business Intelligence project built on the Brazilian Olist e-commerce dataset.

The solution combines Python EDA, PostgreSQL data modeling, advanced SQL, a fan-out-safe analytical model, DAX, and a completed six-page Power BI dashboard.

**Tech stack:** PostgreSQL · SQL · Python · Pandas · Jupyter · Power BI · DAX

![Executive Overview](images/Executive_overview.png)

## What this project demonstrates

- Reproducible raw → staging → analytics → reporting SQL pipeline
- Data-quality profiling and documented edge cases
- Separate fact grains that prevent item/payment fan-out
- Business KPI definitions reconciled between SQL and DAX
- Power BI semantic modeling and time intelligence
- Statistical validation of the delivery/satisfaction relationship
- Business recommendations grounded in observed evidence

## Executive findings

- On-time orders average about **4.29** in review score versus **2.57** for late deliveries when the comparison is restricted to orders with valid delivery dates.
- Repeat customers represent only **3.12%** of the customer base, but generate more revenue per customer than one-time buyers.
- Revenue is geographically concentrated, led by São Paulo, while delivery performance and customer satisfaction vary materially across regions and states.

## Architecture

```text
Raw Olist CSVs
   ↓
Python / Jupyter EDA
   ↓
PostgreSQL raw schema
   ↓
Data-quality checks + staging
   ↓
Analytics schema: 5 dimensions + 3 fact tables
   ↓
Reporting views / business queries
   ↓
Power BI semantic model + DAX
   ↓
6-page dashboard + business insights
```

## Dataset

The project uses the [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).

The repository includes the **9 original CSV files** under:

```text
data/raw/
```

The data contains real, anonymized commercial activity from Olist Store and covers orders placed between **2016-09-04 and 2018-10-17**.

The first months of 2016 and the final months of 2018 contain limited activity. For time-series analysis, the project therefore uses the reliable complete-month window:

**2017-01 through 2018-08**

See [Data quality notes](docs/data_quality_notes.md) for the detailed temporal-quality assessment.

### Raw files

| File | Rows | Grain |
|---|---:|---|
| `olist_orders_dataset.csv` | 99,441 | 1 order |
| `olist_order_items_dataset.csv` | 112,650 | 1 item within an order |
| `olist_order_payments_dataset.csv` | 103,886 | 1 payment transaction within an order |
| `olist_order_reviews_dataset.csv` | 99,224 | 1 review of an order |
| `olist_customers_dataset.csv` | 99,441 | 1 order-level customer ID |
| `olist_products_dataset.csv` | 32,951 | 1 product |
| `olist_sellers_dataset.csv` | 3,095 | 1 seller |
| `olist_geolocation_dataset.csv` | 1,000,163 | 1 geolocation sample per ZIP-code prefix |
| `product_category_name_translation.csv` | 71 | 1 category translation |

### Customer identity

The Olist dataset contains two different customer identifiers:

- `customer_id` — order-level customer identifier
- `customer_unique_id` — persistent customer identity across orders

All customer-level metrics in this project use `customer_unique_id`.

## Data model

### Dimensions

- `dim_date`
- `dim_geography` — customer/shipping geography
- `dim_customer`
- `dim_seller`
- `dim_product`

### Facts

- `fact_orders` — one row per order
- `fact_order_items` — one row per `(order_id, order_item_id)`
- `fact_payments` — one row per `(order_id, payment_sequential)`

The different fact grains are deliberate.

One order can contain multiple items and multiple payment transactions. A naive item × payment join would multiply rows and silently overstate revenue, freight, and payment metrics.

The semantic model therefore keeps order-, item-, and payment-level facts separate.

## Headline KPI references

| KPI | Reference value |
|---|---:|
| Net Revenue | R$ 13,494,400.74 |
| Gross Revenue | R$ 13,591,643.70 |
| Valid Orders (excl. canceled/unavailable) | 98,207 |
| Customers (`customer_unique_id`) | 96,096 |
| AOV | R$ 137.41 |
| Freight as % of Net Revenue | ~16.61% |
| Repeat Customer Rate | 3.12% |
| Avg Review Score | ~4.09 / 5 |
| Late Delivery Rate | ~8.11% |

Dashboard cards can differ slightly where a page is intentionally filtered to the **Jan 2017 – Aug 2018** analysis window.

## Power BI dashboard

The completed Power BI report is included in the repository:

[Open / download the Power BI report](powerbi/olist_business_intelligence.pbix)

### Dashboard pages

1. **Executive Overview**
2. **Sales Performance**
3. **Customer Analytics**
4. **Product & Category Performance**
5. **Seller Performance**
6. **Delivery & Customer Satisfaction**

### Screenshots

#### Sales Performance

![Sales Performance](images/Sales_performance.png)

#### Customer Analytics

![Customer Analytics](images/Customer_analytics.png)

#### Product & Category Performance

![Product & Category Performance](images/Product_%26_Category_Performance.png)

#### Seller Performance

![Seller Performance](images/Seller_performance.png)

#### Delivery & Customer Satisfaction

![Delivery & Customer Satisfaction](images/Delivery_%26_Customer_Satisfaction.png)

Additional Power BI documentation:

- [Power BI model and connection setup](powerbi/README.md)
- [DAX measures](powerbi/dax_measures.md)

## SQL and analysis layers

The PostgreSQL pipeline is organized into separate layers:

- `sql/01_schema/` — schemas and raw tables
- `sql/02_data_quality/` — row counts, null checks, duplicates, referential checks
- `sql/03_cleaning/` — staging and cleaning logic
- `sql/04_dimensions/` — analytical dimensions
- `sql/05_facts/` — analytical fact tables
- `sql/06_reporting_views/` — validated reporting views
- `sql/07_business_queries/` — business analysis queries

The exploratory notebook is available at:

[`notebooks/01_exploratory_data_analysis.ipynb`](notebooks/01_exploratory_data_analysis.ipynb)

The notebook is intentionally used as an independent exploration and validation layer rather than as a second production transformation pipeline.

PostgreSQL remains the reproducible transformation, modeling, and reporting source of truth.

## Reproduce locally

### Requirements

- PostgreSQL
- Python
- Jupyter Notebook
- Power BI Desktop

Python dependencies are listed in:

[`requirements.txt`](requirements.txt)

The required raw CSV files are already included under:

```text
data/raw/
```

Run the following commands from the repository root.

### 1. Create the database

```powershell
createdb olist_analytics
```

### 2. Create schemas and raw tables

```powershell
psql -U postgres -d olist_analytics -f sql/01_schema/01_create_schemas.sql
psql -U postgres -d olist_analytics -f sql/01_schema/02_create_raw_tables.sql
```

### 3. Load raw data

```powershell
psql -U postgres -d olist_analytics -f scripts/load_raw_data.sql
```

### 4. Build the staging layer

```powershell
psql -U postgres -d olist_analytics -f sql/03_cleaning/01_staging_products.sql
psql -U postgres -d olist_analytics -f sql/03_cleaning/02_staging_geolocation.sql
psql -U postgres -d olist_analytics -f sql/03_cleaning/03_staging_orders.sql
```

### 5. Build dimensions

Execute the scripts in filename order from:

```text
sql/04_dimensions/
```

### 6. Build fact tables

Execute the scripts in filename order from:

```text
sql/05_facts/
```

### 7. Build reporting views

Execute the scripts in filename order from:

```text
sql/06_reporting_views/
```

### 8. Optional validation and business analysis

Data-quality checks:

```text
sql/02_data_quality/
```

Business analysis:

```text
sql/07_business_queries/
```

The review dataset contains UTF-8 characters that may fail under a Windows-1252 PostgreSQL client configuration.

`scripts/load_raw_data.sql` explicitly sets the client encoding to UTF-8 before loading the data.

## Repository structure

```text
.
├── README.md
├── LICENSE
├── requirements.txt
├── data/
│   ├── raw/              # 9 original Olist CSV files
│   └── README.md
├── notebooks/
│   └── 01_exploratory_data_analysis.ipynb
├── sql/
│   ├── 01_schema/
│   ├── 02_data_quality/
│   ├── 03_cleaning/
│   ├── 04_dimensions/
│   ├── 05_facts/
│   ├── 06_reporting_views/
│   └── 07_business_queries/
├── scripts/
├── docs/
├── insights/
├── images/
└── powerbi/
    ├── README.md
    ├── dax_measures.md
    └── olist_business_intelligence.pbix
```

## Important modeling conventions

- Use `customer_unique_id` for customer-level metrics.
- Net revenue excludes `canceled` and `unavailable` orders.
- Product/category analysis uses `fact_order_items`.
- Seller analysis uses `fact_order_items`.
- Payment analysis uses `fact_payments`.
- `dim_geography` represents customer geography only.
- Seller geography comes directly from `dim_seller`.
- On-time vs late satisfaction comparisons use only orders with valid delivery dates.
- Avoid fact-to-fact relationships.
- Avoid row-level item/payment joins that would create fan-out.
- Category and seller revenue use the same net-order filtering logic as the main revenue KPI.

## Documentation

- [Data README](data/README.md)
- [Data quality notes](docs/data_quality_notes.md)
- [Star schema design](docs/star_schema_design.md)
- [KPI definitions](docs/kpi_definitions.md)
- [Business insights](insights/business_insights.md)
- [Recommendations](insights/recommendations.md)
- [Power BI model documentation](powerbi/README.md)
- [DAX measures](powerbi/dax_measures.md)

## License

This project is distributed under the terms described in [LICENSE](LICENSE).
