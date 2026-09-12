# Business Recommendations (Phase 10)

Each recommendation follows: **Insight → Business Implication →
Recommendation → Expected Impact → Metric to Monitor**. Expected impact
is stated only using benchmarks already observed in this dataset (never
an invented industry percentage) — where no internal benchmark exists,
that limitation is stated explicitly instead of a fabricated number.

---

### 1. Late deliveries are the strongest driver of dissatisfaction found

- **Insight:** on-time orders average a 4.29 review score; late orders
  average 2.57 (7,825 orders, 8.11% of deliveries).
- **Business implication:** delivery reliability is a bigger lever on
  customer perception than product, price or category — meaning
  logistics investment likely has a higher satisfaction ROI than
  catalog or pricing initiatives.
- **Recommendation:** identify and prioritize the carriers/sellers with
  the highest concentration of late deliveries (already surfaced per
  seller in `reporting.vw_seller_performance`) for corrective action —
  renegotiated SLAs, carrier replacement, or stricter `shipping_limit_date`
  enforcement.
- **Expected impact:** the 4.29 score is not a hypothetical target — it
  is the score this same platform already achieves for 91.9% of
  deliveries. Closing even part of the gap between the 2.57 late-order
  average and the 4.29 on-time average, for a subset of the 7,825 late
  orders, is a realistic, internally-benchmarked goal (no external
  assumption required).
- **Metric to monitor:** `Late Delivery %` and `Avg Review Score
  On-Time` vs. `Late` (both already defined in `powerbi/dax_measures.md`),
  tracked monthly.

### 2. One in five active sellers sits in a revenue/satisfaction risk quadrant — and they're not small

- **Insight:** 639 of 3,053 active sellers (20.9%) combine above-median
  revenue with below-average review scores — and together they account
  for **R$5,287,093.62, or 39.18% of all seller-side revenue**.
- **Business implication:** this is not a fringe problem. A large share
  of platform revenue runs through sellers whose performance is
  actively working against retention — a churn and reputation risk
  concentrated in a specific, identifiable list of sellers.
- **Recommendation:** build a seller account-management program
  targeting this specific 639-seller list first (not sellers in
  general): structured performance reviews, delivery-time SLAs tied to
  marketplace visibility/ranking, and support to fix root causes before
  considering deprioritizing them in search/recommendation placement.
- **Expected impact:** cannot be quantified in revenue terms without
  assuming a specific improvement rate this data doesn't provide — but
  the R$5.29M revenue exposure itself is the business case for
  prioritizing this list over an undifferentiated seller-quality
  initiative.
- **Metric to monitor:** count and revenue share of sellers in the risk
  quadrant, tracked quarterly as a cohort (does the list shrink?).

### 3. `office_furniture` underperforms on satisfaction relative to its own revenue tier

- **Insight:** R$273,580.70 in revenue (top-20 category) with a 3.62
  average review score — the lowest of any top-20 category, 0.47 points
  below the platform average.
- **Business implication:** the issue is specific to this category
  (product quality, packaging/damage in transit, or seller mix within
  it), not a platform-wide delivery problem — it needs its own
  investigation, not a generic fix.
- **Recommendation:** audit the sellers and products within
  `office_furniture` specifically (join `fact_order_items` +
  `dim_seller` + `dim_product` filtered to this category) to determine
  whether the low score concentrates in a few sellers/products or is
  spread evenly across the category.
- **Expected impact:** not quantifiable without the audit's findings —
  stated as the next diagnostic step, not a guessed outcome.
- **Metric to monitor:** `Avg Review Score` filtered to
  `category_name_en = "office_furniture"`, tracked monthly.

### 4. Repeat customers are worth pursuing — the unit economics are already visible

- **Insight:** repeat customers (3.12% of the base) average R$258.40 in
  lifetime revenue vs. R$138.28 for one-time buyers — a R$120.12
  per-customer difference, already observed, not projected.
- **Business implication:** converting even a modest share of the
  93,099 one-time customers into repeat buyers has a known, positive
  per-customer economics — the question is acquisition cost of that
  conversion, which is outside this dataset's scope.
- **Recommendation:** target lifecycle marketing (email/notification
  follow-up, second-purchase incentive) at customers shortly after their
  first delivered order, using `dim_customer.first_order_date` to define
  the outreach window.
- **Expected impact:** R$120.12 in incremental lifetime revenue per
  customer successfully converted to repeat status — this is the
  observed differential in the data, not a forecast; whether outreach
  cost makes this profitable per customer is a marketing-economics
  question this dataset cannot answer.
- **Metric to monitor:** `Repeat Customer Rate` (currently 3.12%),
  tracked monthly as a trend, not a one-time snapshot.

### 5. Delivery speed and revenue are both concentrated in São Paulo — expansion should target supply, not just demand

- **Insight:** SP customers generate 38.37% of revenue with 8.8-day
  average delivery; RJ (13.4% of revenue) averages 15.3 days; BA (3.75%)
  averages 19.3 days. Supply is even more concentrated than demand:
  59.74% of all sellers are based in SP.
- **Business implication:** slower delivery outside SP is plausibly a
  supply-chain distance problem (SP-based sellers shipping nationally),
  not a demand or willingness-to-buy problem in other states.
- **Recommendation:** prioritize seller recruitment/onboarding efforts
  in high-revenue, currently slow-delivery states (RJ, BA, and similarly
  underserved Nordeste states) to shorten shipping distance for local
  demand, rather than only marketing to customers there.
- **Expected impact:** cannot be quantified without knowing recruitment
  cost and take-up — the observed SP benchmark (8.8 days) is the
  internal proof that shorter in-state seller-to-customer distance
  correlates with faster delivery, which is the basis for the
  recommendation.
- **Metric to monitor:** `Avg Delivery Days` by state, and seller count
  by state, tracked together (does delivery time fall as local seller
  count rises?).

### 6. Freight cost inequity by region is a pricing/competitiveness risk outside the Southeast

- **Insight:** freight is 22.74% of item revenue in Norte and 21.74% in
  Nordeste, vs. 15.16% in Sudeste.
- **Business implication:** customers in Norte/Nordeste face a
  meaningfully higher effective price for the same goods, which likely
  suppresses demand growth in those regions relative to the Southeast.
- **Recommendation:** evaluate a regional freight subsidy or a
  negotiated flat-rate shipping tier for Norte/Nordeste orders,
  funded by the fact that Sudeste (67,296 of ~98,000 orders) already
  carries the platform's volume economics.
- **Expected impact:** not quantifiable without knowing price
  elasticity of demand in those regions — stated as a hypothesis this
  data supports (the cost disparity is real) but cannot size on its own.
- **Metric to monitor:** `Freight % of Revenue` by region, alongside
  order volume growth by region (to see if narrowing the gap correlates
  with demand growth there).

### 7. Credit card installments are the platform's only real financing lever

- **Insight:** credit card averages 3.51 installments and 78.3% of
  total payment value; boleto/voucher/debit average ~1.00 installments.
- **Business implication:** any strategy relying on "buy now, pay over
  time" to lift AOV or conversion has, in practice, only one payment
  method to work through.
- **Recommendation:** ensure checkout UX prominently surfaces
  installment options for credit card, and evaluate partnerships that
  could extend similar financing to boleto users (a large share of
  volume, R$2.87M, currently paid in full).
- **Expected impact:** not quantifiable — this dataset shows the current
  mix, not a causal test of what happens if boleto gained installments.
- **Metric to monitor:** `Avg Installments` and `AOV` by `payment_type`,
  tracked to detect any shift if boleto financing were introduced.

### 8. Retention KPIs should be read in the context of a high-growth phase

- **Insight:** the only valid year-over-year comparison (Jan-Aug 2017
  vs. Jan-Aug 2018) shows +138.31% revenue growth — this is a platform
  in aggressive acquisition mode, not a mature, stable marketplace.
- **Business implication:** the 3.12% repeat rate should not be judged
  against a mature-marketplace benchmark; a business growing this fast
  is, by construction, adding new customers faster than existing ones
  accumulate a second purchase within the observed window.
- **Recommendation:** track repeat rate as a **cohort metric** (repeat
  rate of customers acquired in month X, measured 6/12 months later)
  rather than a single point-in-time snapshot, so retention trends
  aren't confounded by the acquisition growth rate.
- **Expected impact:** not a revenue projection — a methodology
  correction so future retention analysis isn't misread.
- **Metric to monitor:** cohort-based repeat rate by acquisition month.

### 9. Seasonal demand spikes strain delivery performance — plan capacity ahead of them

- **Insight:** the late-delivery rate jumped to 14.31% in November 2017
  (the Black Friday month), more than double the 5.18-5.29% rate seen
  in September-October, before partially recovering to 8.38% in
  December and 6.56% in January 2018.
- **Business implication:** the November revenue spike (+52.06% MoM,
  Phase 9) came at a real, measurable operational cost — delivery
  performance degraded exactly when volume peaked, which plausibly also
  degraded satisfaction for that cohort (consistent with finding #1).
- **Recommendation:** treat November capacity (carrier allocation,
  seller shipping-time buffers, `shipping_limit_date` enforcement) as a
  planned seasonal event, not business as usual — pre-negotiate carrier
  capacity ahead of the season based on the prior year's volume pattern.
- **Expected impact:** if capacity planning brought November's late rate
  down toward the 5-6% baseline seen in adjacent months, that is an
  internally-observed, already-achieved performance level for this
  platform — not a hypothetical external target.
- **Metric to monitor:** `Late Delivery %` specifically for November
  (or any month with a similar MoM revenue spike), tracked year over
  year as more seasons of data become available.
