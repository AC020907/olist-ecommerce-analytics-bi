# Business Insights

Observed results only. Every number is reproducible from the warehouse
(`python -m olist_bi build`) with the SQL cited under each finding.
Explanations, hypotheses and actions are in
[`recommendations.md`](recommendations.md).

**Read these as associations.** The data is a historical, anonymized
public sample with no experiments, costs or margins; none of the
differences below proves that changing one factor would change the
outcome.

Definitions used throughout (see [`docs/KPI_RECONCILIATION.md`](../docs/KPI_RECONCILIATION.md)):
net revenue = item prices on orders not `canceled`/`unavailable`;
**late** = delivered on a later calendar day than the promised date,
among delivered orders with valid dates (96,446 orders).

---

## 1. Late orders receive much lower reviews, and the gap grows with the delay

| Delivery vs. promised date | Orders | Avg review | 1–2 star reviews |
|---|---:|---:|---:|
| On time or early | 89,913 | 4.29 | 9.2% |
| 1 day late | 825 | 3.73 | 19.6% |
| 2–3 days late | 1,045 | 2.94 | 41.5% |
| 4–7 days late | 1,801 | 2.10 | 65.6% |
| 8–14 days late | 1,478 | 1.67 | 78.4% |
| 15+ days late | 1,384 | 1.73 | 75.4% |

6,533 orders (6.77%) were late. The on-time vs. late gap (4.29 vs 2.27,
2.02 points) is larger than the spread between product categories with
500+ orders (3.62 to 4.50) or between payment methods (4.02 to 4.17).

*SQL: `07_business_queries/06_delay_vs_review_score.sql`; buckets from
`demo/data/delivery_buckets.parquet` (`olist_bi/export_demo.py`).*

## 2. Late deliveries concentrate in a few months

The monthly late rate was 2.8–3.0% in May–Aug 2017, rose to **12.4%** in
Nov 2017 (the month revenue grew +52.1%), and peaked at **14.1%** (Feb 2018)
and **19.0%** (Mar 2018). It was back to 4.5% in Apr 2018.

*SQL: `07_business_queries/05_delivery_time_and_late_rate.sql`.*

## 3. Delivery time and late rate differ sharply by customer state

| State | Share of net revenue | Avg delivery days | Late rate | Avg review |
|---|---:|---:|---:|---:|
| SP | 38.3% | 8.8 | 4.5% | 4.21 |
| RJ | 13.4% | 15.3 | 12.1% | 3.90 |
| MG | 11.7% | 12.0 | 4.6% | 4.16 |
| BA | 3.8% | 19.3 | 12.1% | 3.88 |
| MA | 0.9% | 21.5 | 17.2% | 3.80 |
| AL | 0.6% | 24.6 | 21.5% | 3.76 |

59.7% of sellers are based in SP.

*SQL: `reporting.vw_customer_geography_performance`, `analytics.dim_seller`.*

## 4. Freight weighs more on revenue outside the Southeast

Freight is 22.7% of net item revenue for Norte customers and 21.7% for
Nordeste, versus 15.2% in Sudeste (which holds 67,299 of 98,207 valid orders).

*SQL: `analytics.fact_orders` → `dim_customer` → `dim_geography`, valid orders.*

## 5. A fifth of active sellers combine above-median revenue with below-average reviews

620 of 3,053 active sellers (20.3%) have revenue above the median seller
(R$825) and an average review below the platform average (4.09). Together
they hold R$5.04M, 37.3% of seller revenue. Applying a stricter screen —
30+ orders, late rate above 10% and average review below 3.8 — leaves
**41 sellers holding R$462K**.

*SQL: `reporting.vw_seller_performance` (median via `PERCENTILE_CONT`).*

## 6. `office_furniture` is a high-revenue category with low reviews

R$273,580.70 of revenue (inside the top 20 categories) with an average
review of 3.62 over 1,272 orders, the lowest of the top 20 and 0.47 below
the platform average.

*SQL: `reporting.vw_category_performance`.*

## 7. Few customers buy twice

2,997 of 96,096 unique customers (3.12%) placed more than one order of
any status; counting only valid orders, 2,888 of 94,990 (3.04%). Repeat
customers average R$258.40 of net revenue each versus R$138.28 for
one-time buyers and hold 5.72% of net revenue.

*SQL: `07_business_queries/08_repeat_purchase_rate.sql`.*

## 8. Credit card is the only payment method used in installments

Credit card carries 78.3% of payment value (R$12.54M of R$16.01M, all
order statuses) with 3.51 installments on average; boleto, voucher and
debit card average 1.00.

*SQL: `reporting.vw_payment_method_summary`.*

## 9. Strong growth with one seasonal spike

Jan–Aug 2018 net revenue was R$7,341,037.41 vs R$3,080,850.81 in
Jan–Aug 2017 (**+138.3%**), the only comparable window. November 2017
grew +52.1% month over month and December fell −26.1%; no other month in
Jan 2017–Aug 2018 moved that much.

*SQL: `reporting.vw_monthly_revenue`.*
