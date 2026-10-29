# KPI Catalogue and Reconciliation Matrix

One definition per KPI, implemented three times: PostgreSQL (`reporting` views /
`analytics` facts), Power BI (DAX in `powerbi/olist_business_intelligence.pbix`)
and the Streamlit demo (`demo/metrics.py` over `demo/data/*.parquet`).

- **Valid order** = `order_status NOT IN ('canceled', 'unavailable')`.
- **Measurable delivery** = delivered order whose carrier and customer dates exist and are in a
  possible order (`is_late IS NOT NULL`; 96,446 orders).
- **Late** = `order_delivered_customer_date::date > order_estimated_delivery_date::date`.
  All 99,441 promised dates carry no time of day, so the promise is a calendar date; a
  delivery at any time on the promised day is on time. (Until 2026-10-29 the rule compared
  the delivery *timestamp* with midnight and counted 1,292 same-day deliveries as late.)
- Money is Brazilian reais (BRL). Values: full dataset, rebuilt 2026-10-29.

## 1. KPI catalogue

| KPI | Business definition | Numerator | Denominator | Population / exclusions | Grain | SQL | DAX measure | Streamlit (`metrics.py`) | Value |
|---|---|---|---|---|---|---|---|---|---:|
| Net Revenue | Product sales actually sold | Σ item price | — | valid orders; excludes freight | order (`fact_orders.items_revenue`) | `vw_executive_summary.net_revenue` | `Total Revenue` | `kpis()["revenue"]` | R$ 13,494,400.74 |
| Gross Revenue | Product value of every order | Σ item price | — | all statuses | order | `.gross_revenue` | `Gross Revenue` | `kpis()["gross_revenue"]` | R$ 13,591,643.70 |
| Total Orders | Orders that were sold | count orders | — | valid orders (incl. 8 with no items) | order | `.total_orders` | `Total Orders` | `kpis()["orders"]` | 98,207 |
| Total Customers | People who placed any order | distinct `customer_unique_id` | — | **all statuses**; 94,990 have ≥1 valid order | customer | `.total_customers` | `Total Customers` | not shown (not additive across filters) | 96,096 |
| AOV | Revenue per order | Net Revenue | Total Orders | valid orders | order | `.avg_order_value` | `AOV` | `kpis()["aov"]` | R$ 137.41 |
| Repeat Customer Rate | Share of people with >1 order | customers with `lifetime_order_count > 1` | all customers | lifetime orders of **any status** (3.04% on valid orders only) | customer | `08_repeat_purchase_rate.sql` | `Repeat Customer Rate` | not shown | 3.12% |
| Late Delivery Rate | Deliveries after the promised day | late orders | measurable deliveries | delivered + valid dates; canceled orders with dates excluded | order | `.late_delivery_rate_pct` | `Late Delivery %` | `kpis()["late_pct"]` | 6.77% |
| Avg Delivery Days | Purchase → customer delivery | Σ `delivery_days` | measurable deliveries | delivered + valid dates | order | `.avg_delivery_days` | `Avg Delivery Days` | `kpis()["delivery_days"]` | 12.6 days |
| Avg Review Score | Customer satisfaction | Σ order review (multi-review orders averaged first) | reviewed orders | all statuses with a review | order | `.avg_review_score` | `Avg Review Score` | `kpis()["review"]` | 4.09 |
| Review On-Time / Late | Satisfaction by delivery outcome | Σ review | reviewed measurable deliveries | `is_late` false / true (blank excluded) | order | `06_delay_vs_review_score.sql` | `Avg Review Score On-Time` / `Late` | delivery buckets | 4.29 / 2.27 |
| Total Freight | Shipping charged on sold orders | Σ freight | — | valid orders | order | `.total_freight` | `Total Freight` | `kpis()["freight"]` | R$ 2,241,126.29 |
| Freight % of Revenue | Shipping weight on the basket | Total Freight | Net Revenue | valid orders | order | `.freight_pct_of_revenue` | `Freight % of Revenue` | `kpis()["freight_pct"]` | 16.61% |
| Category Revenue | Sales by product category | Σ item price | — | valid orders | item (`fact_order_items`) | `vw_category_performance.revenue` | `Item Revenue` sliced by `dim_product` | `category_table()` | Σ = Net Revenue |
| Seller Revenue | Sales by seller | Σ item price | — | valid orders | item | `vw_seller_performance.revenue` | `Seller Revenue` | `seller_table()` | Σ = Net Revenue |
| Payment Method Distribution | Share of payment value by method | Σ payment value per type | Σ payment value | **all statuses** (R$ 16.01M; R$ 15.74M on valid orders) | payment | `vw_payment_method_summary` | `Payment Share %` | not shown | credit card 78.3% |

Legitimate differences that are **not** reconciliation errors:

- **Payments ≠ revenue + freight.** On valid orders payments are R$ 15,739,137.01 vs
  items + freight R$ 15,735,527.03 (0.02% gap: vouchers and installment interest). Checked by
  `payments_vs_items_plus_freight` with a 0.1% tolerance.
- **Customers and repeat rate use all statuses** while revenue uses valid orders; both
  populations are stated wherever the numbers are quoted.
- **Category and seller review scores** are averaged over distinct (category, order) or
  (seller, order) pairs, so a multi-seller order counts once per seller.
- **Geography** is the ZIP of the customer's most recent order mapped through `dim_geography`;
  268 customers (272 valid orders, R$ 36,199.13) fall into `Unknown`.

## 2. Reconciliation matrix

PostgreSQL = SQL against `analytics`/`reporting`; Power BI = DAX query against the open
`.pbix` model through the Power BI modeling MCP server; Streamlit = `demo/metrics.py` on the
committed parquet files. Tolerance: exact to the cent for money, 1e-9 relative for ratios.

| Scenario | KPI | PostgreSQL | Power BI | Streamlit | Status |
|---|---|---:|---:|---:|---|
| No filter | Net Revenue | 13,494,400.74 | 13,494,400.74 | 13,494,400.74 | ✓ |
| | Orders | 98,207 | 98,207 | 98,207 | ✓ |
| | AOV | 137.41 | 137.41 | 137.41 | ✓ |
| | Total Freight | 2,241,126.29 | 2,241,126.29 | 2,241,126.29 | ✓ |
| | Avg Review | 4.0868 | 4.0868 | 4.0868 | ✓ |
| | Avg Delivery Days | 12.559 | 12.559 | 12.559 | ✓ |
| | Late Delivery % | 6.7737% | 6.7737% | 6.7737% | ✓ |
| | Review on-time / late | 4.291 / 2.271 | 4.291 / 2.271 | 4.29 / 2.27 (delivery buckets) | ✓ |
| | Item Revenue / Items | 13,494,400.74 / 112,101 | 13,494,400.74 / 112,101 | = | ✓ |
| | Customers / Repeat rate | 96,096 / 3.12% | 96,096 / 3.12% | n/a | ✓ |
| Date: Jan–Jun 2018 | Net Revenue | 5,614,133.04 | 5,614,133.04 | 5,614,133.04 | ✓ |
| | Orders / AOV | 40,877 / 137.34 | 40,877 / 137.34 | 40,877 / 137.34 | ✓ |
| | Freight | 942,247.37 | 942,247.37 | 942,247.37 | ✓ |
| | Avg Review / Delivery days | 4.0376 / 13.318 | 4.0376 / 13.318 | 4.0376 / 13.318 | ✓ |
| | Late Delivery % | 8.6342% | 8.6342% | 8.6342% | ✓ |
| Region: Nordeste | Net Revenue | 1,532,758.69 | 1,532,758.69 | 1,532,758.69 | ✓ |
| | Orders / AOV | 9,277 / 165.22 | 9,277 / 165.22 | 9,277 / 165.22 | ✓ |
| | Freight | 333,235.19 | 333,235.19 | 333,235.19 | ✓ |
| | Avg Review / Delivery days | 3.8969 / 19.983 | 3.8969 / 19.983 | 3.8969 / 19.983 | ✓ |
| | Late Delivery % | 12.676% | 12.676% | 12.676% | ✓ |
| Region: Unknown | Net Revenue / Orders | 36,199.13 / 272 | (Blank) bucket | 36,199.13 / 272 | ✓ SQL = Streamlit |
| Status (gross) | Gross Revenue | 13,591,643.70 | 13,591,643.70 | 13,591,643.70 | ✓ |
| Category: health_beauty | Revenue / Items | 1,255,695.13 / 9,634 | 1,255,695.13 / 9,634 | 1,255,695.13 / 9,634 | ✓ |
| Seller: top seller `4869f7a5…` | Revenue / Orders | 229,237.63 / 1,131 | 229,237.63 / 1,131 | 229,237.63 / 1,131 | ✓ |

Automated coverage (`tests/test_kpi_reconciliation.py`, run in CI on the full dataset):
SQL vs Streamlit for 7 date/region/state filter combinations, all 74 categories, the top
200 sellers, the empty selection and the reference KPI file. Power BI values were taken with
DAX queries; Power BI Desktop cannot run in CI.

## 3. Power BI status

Verified 2026-10-29 by closing and reopening the saved `.pbix` and querying it:

- the nine corrected measures (`Avg Review Score On-Time`, `Avg Review Score Late`,
  `Late Delivery %`, `Total Freight`, `Avg Items per Order`, `Item Revenue`, `Items Sold`,
  `Avg Item Price`, `Seller Revenue`) are stored in the file;
- the imported data was refreshed from a warehouse built with the calendar-date rule
  (6.7737% late, 4.291 on-time vs 2.271 late review, R$ 13,494,400.74, R$ 2,241,126.29 freight);
- the data source is the standard `PostgreSQL.Database("localhost", "olist_analytics")`.

Report fixes in the same pass: the Executive Overview page had a hidden page filter
`region is not (Blank)` that dropped 272 orders (R$ 36,199.13), so its card showed
R$ 13.41M instead of R$ 13.45M for Jan 2017–Aug 2018; the filter was removed and the
unmapped customers appear as "(Blank)". The Sales and Customer pages' subtitles now say
which visuals use all orders and which use the Jan 2017–Aug 2018 window.
`powerbi/olist_business_intelligence.pdf` is an export of the saved report.
