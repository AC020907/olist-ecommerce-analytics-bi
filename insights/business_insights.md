# Business Insights (Phase 9)

Every number below is a real, reproducible result from the star schema
built in Phases 3-6 — re-run the referenced SQL to verify any of them.
This document is insights only, per the project's methodology:
recommendations (insight → implication → action → expected impact →
metric to monitor) are in `insights/recommendations.md` (Phase 10).

---

## 1. Late deliveries are the single strongest driver of dissatisfaction found in the data

Orders delivered on time average a **4.29** review score; orders
delivered late average **2.57** — a 1.72-point gap on a 5-point scale,
across 7,825 late orders (8.11% of the 96,446 orders with a valid
delivery record). No other segmentation in this project — category,
payment method, or seller — produces a gap remotely this large,
suggesting that delivery reliability, not product or price, is the
primary lever on customer satisfaction in this marketplace.

*Source: `analytics.fact_orders`, grouped by `is_late`.*

## 2. 20.9% of active sellers combine above-median revenue with below-average satisfaction

639 of 3,053 sellers with at least one sale generate more than the
median seller revenue (R$825) while scoring below the platform's
overall average review score (4.09). This is not a marginal group —
it's one in five active sellers — suggesting that a meaningful share of
platform revenue currently runs through sellers whose fulfillment or
product quality is actively working against customer retention rather
than for it.

*Source: `reporting.vw_seller_performance`, median via `PERCENTILE_CONT`.*

## 3. `office_furniture` generates real revenue (R$273,580.70) while scoring well below the platform average

Among the top-20 categories by revenue, `office_furniture` is the clear
outlier: its 3.62 average review score sits 0.47 points below the
platform average (4.09) and is the lowest of any category in that top
20 — while its revenue (R$273,580.70) puts it comfortably inside the
top half. This is the concrete answer to "which category combines high
revenue with low satisfaction" — not a category with a marginally lower
score, but a specific, identifiable one.

*Source: `reporting.vw_category_performance`.*

## 4. Repeat customers are 3.12% of the customer base but generate 5.72% of revenue and spend ~87% more per head

2,997 of 96,096 real customers (`customer_unique_id`) placed more than
one order. That small group's average lifetime revenue is R$258.40,
versus R$138.28 for one-time customers — 1.87x higher. Repeat customers
therefore contribute a share of revenue (5.72%) disproportionate to
their share of the customer base (3.12%), even though the absolute
repeat rate is low in market terms.

*Source: `analytics.dim_customer.is_repeat_customer` joined to
`fact_orders`, aggregated by customer.*

## 5. São Paulo delivers in roughly half the time of the next-largest states, and concentrates both supply and demand — unequally

Customers in SP generate 38.27% of total revenue with an average
delivery time of **8.8 days**; RJ (13.4% of revenue) averages 15.3
days, and BA (3.75% of revenue) averages 19.3 days — more than double
SP's delivery time. This lines up with the supply side: 59.74% of all
sellers are based in SP, versus only 38.27% of revenue coming from SP
customers — sellers are more concentrated in SP than demand is,
meaning a majority of orders placed outside SP are shipped from a
seller based somewhere else in the country, which is consistent with
the longer delivery times observed outside SP/Sudeste.

*Source: `reporting.vw_customer_geography_performance`,
`analytics.dim_seller`.*

## 6. Freight cost as a share of revenue is 50% higher in the North than in the Southeast

Freight represents 22.74% of item revenue for customers in the Norte
region and 21.74% in Nordeste, versus 15.16% in Sudeste — the region
that also has the shortest delivery times and the highest seller
concentration. Customers in Brazil's less economically central regions
pay proportionally more to receive the same kind of goods, and appear
to wait longer for them.

*Source: `analytics.fact_order_items` joined through `dim_customer` /
`dim_geography`.*

## 7. Credit card is the only payment method Brazilian customers use to finance a purchase over time

Credit card carries an average of 3.51 installments and represents
R$12.54M of the R$16.01M in total captured payments (78.3%); boleto,
voucher and debit card average almost exactly 1.00 installments each
— they are essentially always paid in full immediately. Any pricing or
promotion strategy involving payment plans has, in practice, only one
real channel to work through.

*Source: `reporting.vw_payment_method_summary`.*

## 8. Demand grew explosively year over year, but the only valid comparison window is 8 months

Comparing the only overlapping period with reliable data — Jan-Aug 2017
vs. Jan-Aug 2018 — net revenue grew from R$3,080,850.81 to
R$7,341,037.41, a **+138.31%** year-over-year increase. This reflects a
platform still in a high-growth phase during the period captured by
this dataset, not a mature, stable marketplace — a distinction that
matters for interpreting any of the other insights here (e.g. the low
3.12% repeat rate is more explainable in a fast-growing, still
customer-acquisition-heavy business).

*Source: `analytics.fact_orders` joined to `analytics.dim_date`,
filtered to month <= 8 for both years — see `docs/kpi_definitions.md`
for why a full-year comparison isn't possible with this dataset.*

## 9. Revenue has a clear, singular seasonal peak, not steady seasonality

November 2017 revenue grew +52.06% month-over-month (Black Friday),
immediately followed by a -26.07% pull-back in December. No other month
in the 2017-01/2018-08 window shows a swing anywhere near this size in
either direction. Demand in this dataset is better described as
"steady growth with one seasonal event," not as a business with regular
recurring seasonal cycles.

*Source: `reporting.vw_monthly_revenue`.*
