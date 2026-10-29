# Business Recommendations

Each recommendation follows **Finding → Evidence → Interpretation →
Hypothesis → Recommended action → KPI to track**. Findings and evidence
are observed in the data ([`business_insights.md`](business_insights.md)).
Interpretations and hypotheses are **not proven**: this is a historical,
observational dataset without experiments, costs, margins or marketing
spend, so no recommendation below claims a revenue or satisfaction gain.
Where a decision would need causal evidence, the action is the
experiment or analysis that would produce it.

---

### 1. Treat on-time delivery as a customer-experience KPI, and test whether it moves reviews

- **Finding:** late orders are reviewed far worse than on-time orders.
- **Evidence:** 4.29 vs 2.27 average review (6,533 late of 96,446 measurable
  deliveries); the average falls from 3.73 at one day late to 1.67–1.73 at 8+ days.
- **Interpretation:** the dose-response pattern (worse with each extra day)
  is consistent with lateness itself hurting satisfaction, but late orders
  also differ in seller, region and product, which could explain part of
  the gap.
- **Hypothesis:** reducing late deliveries — or setting promised dates the
  logistics network can meet — would raise average reviews.
- **Recommended action:** (1) re-estimate the gap within the same seller and
  category to remove the obvious confounders; (2) A/B test more conservative
  promised dates for a share of orders in high-late states and compare
  review scores and conversion.
- **KPI to track:** weekly late-delivery rate; average review for on-time vs
  late orders; share of 1–2 star reviews.

### 2. Plan delivery capacity ahead of demand peaks

- **Finding:** late deliveries cluster in a few high-volume months.
- **Evidence:** 2.8–3.0% late in May–Aug 2017, 12.4% in Nov 2017, 14.1% in
  Feb 2018 and 19.0% in Mar 2018.
- **Interpretation:** the Nov 2017 spike coincides with Black Friday volume;
  Feb–Mar 2018 volume (6,600–7,200 orders) was similar to Jan and Apr–May 2018, which had normal late rates, so volume alone
  does not explain it (carrier disruptions are one possibility the data
  cannot confirm).
- **Hypothesis:** carrier and seller capacity do not scale with peak volume.
- **Recommended action:** monitor the late rate weekly with an alert
  threshold (e.g. twice the trailing 8-week median), and investigate the
  Feb–Mar 2018 episode by carrier and seller before committing to a
  capacity plan.
- **KPI to track:** weekly late rate; orders per active seller; late rate by
  seller state during peak weeks.

### 3. Review a short list of high-volume sellers with poor delivery and ratings

- **Finding:** a small set of sizable sellers combines late deliveries with
  low reviews.
- **Evidence:** 41 sellers with 30+ orders have a late rate above 10% and an
  average review below 3.8 (R$462K of revenue). A looser screen (above-median
  revenue, below-average review) returns 620 sellers and R$5.04M.
- **Interpretation:** the thresholds are a screening rule, not a verdict:
  low ratings can come from product quality, category or customer region,
  not only from the seller's operations.
- **Hypothesis:** for some of these sellers, fulfilment issues (late
  hand-over to the carrier) drive the low ratings.
- **Recommended action:** check each seller's carrier hand-over time against
  `shipping_limit_date` and their review comments; agree corrective plans
  only where the seller's own process is the cause.
- **KPI to track:** number of sellers meeting the screen, quarter over
  quarter; their late rate and average review.

### 4. Diagnose the low satisfaction in `office_furniture`

- **Finding:** a top-20 revenue category has the lowest reviews of the top 20.
- **Evidence:** R$273,580.70 revenue, 3.62 average review (platform 4.09), 1,272 orders.
- **Interpretation:** bulky goods could suffer more damage or delays, but the
  issue could also concentrate in a few sellers or products.
- **Hypothesis:** a small number of sellers or products drives most of the low scores.
- **Recommended action:** break the category's reviews down by seller,
  product and delay bucket (item-grain fact joined to the order-grain review)
  before taking any category-wide action.
- **KPI to track:** average review and late rate for the category, monthly.

### 5. Investigate seller coverage outside São Paulo

- **Finding:** delivery is slower and later outside SP.
- **Evidence:** SP 8.8 days / 4.5% late; RJ 15.3 / 12.1%; BA 19.3 / 12.1%;
  AL 24.6 / 21.5%. 59.7% of sellers are in SP.
- **Interpretation:** distance between SP-based sellers and customers is a
  plausible explanation; carrier coverage and infrastructure are others.
  This dataset has no carrier field to separate them.
- **Hypothesis:** orders served by a seller in the customer's own state or
  region arrive faster.
- **Recommended action:** compare delivery time for same-state vs.
  cross-state seller–customer pairs (both locations are in the model) before
  investing in regional seller recruitment.
- **KPI to track:** average delivery days and late rate by customer state;
  share of orders served by same-region sellers.

### 6. Size freight sensitivity before considering regional freight changes

- **Finding:** freight is a larger share of the basket outside the Southeast.
- **Evidence:** 22.7% of item revenue in Norte, 21.7% in Nordeste, 15.2% in Sudeste.
- **Interpretation:** customers there pay more per real of goods; whether
  this suppresses demand cannot be measured here (no price variation,
  no traffic or conversion data).
- **Hypothesis:** lower freight would increase conversion in Norte/Nordeste.
- **Recommended action:** if the business has conversion data, test a
  freight discount for a random subset of Norte/Nordeste sessions and
  measure conversion and margin; otherwise do not act on this finding alone.
- **KPI to track:** freight % of revenue and orders by region.

### 7. Measure retention by cohort before investing in it

- **Finding:** few customers buy twice.
- **Evidence:** 3.12% repeat (3.04% counting valid orders only); repeat
  customers average R$258.40 vs R$138.28 of net revenue.
- **Interpretation:** the R$120 difference is partly mechanical — repeat
  customers have more orders by definition — so it is not the value that
  converting a one-time buyer would add. The observed window is short and
  the platform grew +138% year over year, which depresses any point-in-time
  repeat rate.
- **Hypothesis:** a second-purchase campaign would raise the repeat rate.
- **Recommended action:** report repeat rate by acquisition-month cohort
  (90/180-day repeat), and run a holdout-controlled post-delivery campaign
  before estimating its value.
- **KPI to track:** 90-day and 180-day cohort repeat rate; incremental
  repeat rate of treated vs. holdout customers.

### 8. Keep payment analysis descriptive

- **Finding:** only credit card is used in installments.
- **Evidence:** 3.51 average installments and 78.3% of payment value;
  other methods average 1.00.
- **Interpretation:** the data shows the current mix only; it cannot show
  what would happen if other methods offered installments.
- **Recommended action:** no change based on this data; if installment
  options are tested, compare AOV and conversion against a control group.
- **KPI to track:** AOV and average installments by payment type.
