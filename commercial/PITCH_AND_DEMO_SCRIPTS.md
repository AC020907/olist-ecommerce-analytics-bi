# Pitch, Demo Script and Explanations

## 60-second pitch (English)

> Most growing online businesses already have the data to answer their key questions — it's just scattered across exports that don't agree with each other. I build the layer in between: I take raw sales, product, customer and delivery data, clean it, model it so revenue is never double-counted, test it automatically, and deliver a dashboard your team can trust every week.
>
> In my public case study I did this with a Brazilian marketplace dataset: about 100,000 orders and 1.5 million rows. The pipeline rebuilds in 30 seconds, 44 automated checks reconcile revenue to the cent, and the dashboard shows where the business grows and where it leaks. For example, late orders averaged 2.27 stars against 4.29 for on-time ones, and late deliveries climbed to 19% in the worst month — exactly the kind of signal an operations manager wants to see weekly, not at the end of the quarter.
>
> I can do the same with your Shopify, ERP or Excel exports, starting with a small fixed-price dashboard so you can judge the result first.

## Demo script (2–3 minutes, screen share of the web demo)

| Time | Screen | What to say |
|---|---|---|
| 0:00 | Header | "This is a demo built on a public e-commerce dataset — about 100k orders from a Brazilian marketplace. Imagine it's your store." |
| 0:15 | Executive overview KPIs | "These five numbers are what I'd put in front of a manager: net revenue, orders, average order value, review score and late deliveries. Net revenue excludes canceled orders and shipping, and that definition is written down so everyone uses the same one." |
| 0:40 | Monthly revenue chart, then filter a region | "Revenue grew steadily through 2017, peaked at Black Friday. If I filter to the North-East… everything updates — revenue, AOV, and you can see the AOV is higher here but late deliveries are almost double." |
| 1:05 | Sales performance | "Here are the categories that drive revenue, and the sellers. The orange dots are sellers with more than 30 orders, a late rate over 10% and ratings under 3.8 — 41 of them. That's a call list for the account team." |
| 1:30 | Delivery & satisfaction | "This is the key chart: on-time orders average 4.3 stars; a week late, 2.1; one to two weeks late, 1.7, and more than three out of four reviews are one or two stars. And late deliveries jump in peak months." |
| 1:55 | Insights & weekly KPIs | "Each insight is calculated live from the filters. Below is the weekly scorecard I'd suggest monitoring." |
| 2:15 | How the numbers are built | "And this is why you can trust it: the demo's numbers match the SQL warehouse exactly, and 44 automated checks run every time the data is rebuilt." |
| 2:35 | Close | "With your data, the first version usually takes one to two weeks. Want to start with the questions you'd like this dashboard to answer?" |

## Technical explanation (job interviews, ~2 minutes)

"The source is nine CSV files from Olist — orders, items, payments, reviews, customers, sellers, products, translations and a million geolocation rows. I load them with Python into a PostgreSQL `raw` schema with real types and constraints, so bad data fails at load time instead of silently propagating.

The `staging` layer handles data-quality decisions explicitly: category fallbacks with a flag, one row per ZIP from the geolocation samples using the mode city and state, and delivery dates marked invalid when they're chronologically impossible, so delivery KPIs are NULL rather than negative.

The `analytics` layer is a star schema with three facts at different grains. The important decision is that an order can have several items and several payments, so I pre-aggregate items, freight, payments and reviews to the order in `fact_orders`, and keep item-level and payment-level facts separate for category, seller and payment analysis. Customers are keyed on `customer_unique_id`, because `customer_id` is regenerated per order.

Quality is enforced with 44 checks: primary and foreign keys, required fields, date logic, money, and reconciliation — gross revenue in the facts equals the raw items to the cent, and net revenue is identical at order grain, item grain and in every reporting view. Pytest rebuilds the warehouse from a small fixture dataset with hand-computed expectations, including a two-item, two-payment order, and checks the rebuild is idempotent.

Power BI imports the star schema. When I audited it against SQL with DAX queries, I found that a filter like `is_late = FALSE()` also matches blanks in DAX, which pulled undelivered orders into the 'on-time' average — 4.21 instead of 4.29. I documented and verified the fix. That's the habit I bring: reconcile every layer against the one below it."

## Plain-language explanation (clients who don't use SQL or Python)

"Your systems record every sale, but in pieces: one file for orders, another for products, another for payments and deliveries. When someone combines them by hand, it's easy to count the same sale twice or include cancellations, and that's why reports disagree.

I build an automatic process that combines those pieces correctly every time, checks the result against totals you already trust, and feeds a dashboard. You open it and see how much you sold, what's growing, which products and regions matter, and where customers are unhappy — without anyone copying data into Excel. If something looks wrong in the source data, the checks flag it before it reaches the dashboard."
