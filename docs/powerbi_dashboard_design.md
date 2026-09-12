# Power BI Dashboard Design (Phase 7)

6 pages, not 7 — "Delivery & Customer Satisfaction" and "Geographic
Analysis" were merged into one page because, in this dataset, the main
satisfaction story IS a geographic/delivery story (see Page 6): keeping
them separate would have produced one thin page repeating the same
handful of numbers. Every other proposed page earned its place with a
real, distinct question the data can answer.

All monetary figures below are **Net Revenue** (excludes
canceled/unavailable orders — see `docs/kpi_definitions.md`) unless
stated otherwise. Real values shown are reference points computed
against the live database; the actual dashboard will recompute them
live via DAX and respond to filters.

---

## Page 1 — Executive Overview

**Objetivo:** que un hiring manager o un gerente entienda la salud del
negocio en menos de 30 segundos.

**KPI cards (top row):** Total Revenue (R$13.49M) · Total Orders
(98,207) · Total Customers (96,096) · AOV (R$137.41) · Avg Review Score
(4.09) · Late Delivery Rate (8.11%).

**Visualizaciones:**
- Line chart: Net Revenue by month, default-filtered to the analysis
  window (2017-01 to 2018-08).
- Bar chart (horizontal, 5 bars): Revenue by Region.
- Matrix: Top 5 categories by revenue (compact, 2 columns: category,
  revenue).

**Filtros/slicers:** date range slicer (defaults to analysis window,
can be expanded), region slicer.

**Drill-down:** date hierarchy (Year → Quarter → Month) on the line
chart.

**Drill-through:** right-click a month → **Sales Performance** page
filtered to that month; right-click a region → **Delivery & Geographic
Analysis** page filtered to that region.

**Tooltips:** hovering the revenue line shows Orders and AOV for that
month (report-page tooltip, not default).

**Interacciones:** the region bar chart cross-filters the line chart and
the category matrix; KPI cards do not filter anything (they're the
constant headline).

**Insight que debe permitir descubrir:** the November 2017 spike
(Black Friday, +52% MoM) and the December pull-back (−26%) are visible
immediately on the line chart without any filter.

---

## Page 2 — Sales Performance

**Objetivo:** entender la tendencia de ventas, estacionalidad y mezcla
de pago con suficiente detalle para explicar el "por qué" detrás del
número del Executive Overview.

**KPI cards:** Total Revenue · MoM Growth % (current month) · AOV ·
Avg Items per Order (1.13).

**Visualizaciones:**
- Line + column combo: Net Revenue (line) and Orders (column) by month.
- Bar chart: Orders by Payment Type, data labels showing Avg
  Installments (credit_card 3.51 vs. 1.00 for the rest).
- Column chart: Revenue by day-of-week (uses `dim_date.day_of_week` /
  `is_weekend`) — an operationally useful, low-cost addition already
  supported by the model.
- Matrix: month-by-month table matching `reporting.vw_monthly_revenue`
  (year_month, revenue, orders, AOV, MoM%) — doubles as the validation
  check that DAX and SQL agree.

**Filtros/slicers:** year slicer, payment type slicer.

**Drill-down:** Year → Quarter → Month → Day on the combo chart.

**Drill-through:** none needed outward from this page (it's a detail
page reached from Executive Overview).

**Tooltips:** payment-type bar tooltip shows total value and % of total.

**Insight:** credit card is the only payment method Brazilian customers
use to finance a purchase over multiple installments (avg 3.51) —
boleto/voucher/debit are essentially always paid in full.

---

## Page 3 — Customer Analytics

**Objetivo:** caracterizar la base de clientes: cuántos son, cuántos
repiten, y si repetir realmente vale más para el negocio (no asumirlo).

**KPI cards:** Total Customers (96,096) · Repeat Customer Rate (3.12%)
· Avg Revenue per Repeat Customer (R$258.40) · Avg Revenue per
One-time Customer (R$138.28).

**Visualizaciones:**
- Bar chart (2 bars, not a donut): Customers by type — New vs. Repeat
  (92,001 vs. 2,997 — do not chart at the same scale as revenue; keep
  as a separate small visual).
- Bar chart: Avg Revenue per Customer, New vs. Repeat — the almost-2x
  gap (R$258.40 vs R$138.28) is the headline of this page.
- Histogram (bucketed bar): Order value distribution (buckets: <50,
  50-100, 100-150, 150-250, 250-500, 500+) — real distribution already
  computed: 29,269 / 28,192 / 16,643 / 13,249 / 7,251 / 3,603 orders.
- Table: Customers by state (top 10, count only — revenue-by-state
  belongs on Page 6, this page stays about customer count/behavior).

**Filtros/slicers:** state slicer, New/Repeat slicer.

**Drill-through:** right-click a state row → **Delivery & Geographic
Analysis** filtered to that state.

**Insight:** repeat customers are only 3.12% of the base but generate
5.72% of total revenue and nearly double the average revenue per head
— a quantified case for a retention/loyalty investment, not a vague
"repeat customers are valuable" claim.

---

## Page 4 — Product & Category Performance

**Objetivo:** identificar qué categorías generan el revenue y si el
precio y la satisfacción se mueven juntos o no.

**KPI cards:** Top category by revenue (health_beauty, R$1.26M) ·
Number of categories with sales · Avg item price (overall).

**Visualizaciones:**
- Bar chart (horizontal, top 15): Revenue by category.
- Scatter plot: Avg Item Price (x) vs. Avg Review Score (y) per
  category, bubble size = Revenue — directly supports business
  question #10 (categories combining high revenue with low
  satisfaction) with real per-category data from
  `reporting.vw_category_performance`.
- Table (sortable): full category detail — items sold, orders, revenue,
  avg price, avg review score.

**Filtros/slicers:** category multi-select slicer, price range slicer.

**Drill-through:** right-click a category → **Seller Performance**
page filtered to sellers of that category (works because
`fact_order_items` links product and seller at the same grain — see
`powerbi/README.md`).

**Insight:** the scatter plot is where a viewer can spot a category
that sells a lot but scores poorly — the same "high revenue, low
satisfaction" lens as Page 5, applied to categories instead of sellers.

---

## Page 5 — Seller Performance & Operational Risk

**Objetivo:** identificar vendedores que representan riesgo
operacional: mucho revenue, mala experiencia de entrega/satisfacción.

**KPI cards:** Active Sellers (3,053 with at least one sale) · Sellers
in the risk quadrant (**639**, verified: above-median revenue AND
below-average review score) · Avg Late Delivery Rate across sellers.

**Visualizaciones:**
- Scatter/quadrant chart: Revenue (x) vs. Avg Review Score (y), bubble
  size = Orders, with reference lines at the median revenue (R$825)
  and the overall avg review score (4.09) — splitting the chart into
  4 quadrants; the top-right-by-revenue/bottom-by-score quadrant is
  the 639-seller risk group, called out with a distinct color.
- Table (top 15 by revenue): seller_id, state, revenue, avg delivery
  days, late delivery %, avg review score — conditional formatting
  (red) on rows with late_delivery_rate_pct above the 8.11% overall
  average.
- Bar chart: Seller count / revenue by state (seller-side geography —
  distinct from Page 6's customer-side geography).

**Filtros/slicers:** state slicer, minimum-orders threshold slicer (to
exclude single-sale sellers from the scatter plot as noise).

**Drill-through:** right-click a seller's state → **Delivery &
Geographic Analysis** filtered to that state.

**Insight:** 639 of 3,053 active sellers (20.9%) sit in the risk
quadrant — a concrete, sized target list for account management, not
an abstract warning.

---

## Page 6 — Delivery & Geographic Analysis

**Objetivo:** responder directamente si los retrasos de entrega afectan
la satisfacción, y dónde se concentra el problema geográficamente.

**KPI cards:** Avg Delivery Days (12.6) · Late Delivery Rate (8.11%) ·
Avg Review Score, On-Time (**4.29**) vs. Late (**2.57**) — a 1.72-point
gap on a 5-point scale, the strongest single relationship found in this
dataset.

**Visualizaciones:**
- Filled Map (Power BI's built-in map, geographic role = State,
  Country = Brazil) OR a bubble map using `dim_geography` avg lat/lng
  aggregated to state level if the filled map's auto-geocoding of
  Brazilian states is unreliable — color = Avg Delivery Days, size =
  Revenue.
- Column chart (2 columns): Avg Review Score, On-Time vs. Late — the
  simplest, most direct chart on the whole dashboard, and the one
  that makes the case in one glance.
- Bar chart: Late Delivery Rate by state, sorted descending.
- Scatter plot: Avg Delivery Days (x) vs. Avg Review Score (y) by
  state, bubble size = Orders — shows SP as fast (8.8 days) and
  high-volume, RJ/BA as slower (15.3 / 19.3 days).

**Filtros/slicers:** region slicer, state slicer.

**Interacciones:** the map cross-filters the bar chart and scatter
plot.

**Insight:** delivery delay is the single clearest driver of
dissatisfaction found in the data (4.29 vs. 2.57 avg score) — stronger
and more actionable than any category-level or seller-level pattern,
and directly ties to the state-level concentration also shown on this
page.

---

## Cross-page navigation summary

```
Executive Overview
  ├─ drill-through (month)  → Sales Performance
  └─ drill-through (region) → Delivery & Geographic Analysis

Customer Analytics
  └─ drill-through (state)  → Delivery & Geographic Analysis

Product & Category Performance
  └─ drill-through (category) → Seller Performance

Seller Performance
  └─ drill-through (seller state) → Delivery & Geographic Analysis
```

No circular drill-throughs, and every page can also be reached directly
from the page navigator — drill-through is a shortcut for "I saw
something interesting here, show me more," never the only path.

## Visuals deliberately NOT used

- **Pie/donut charts:** replaced with bar charts everywhere (New vs.
  Repeat customers, payment type mix) — bars make magnitude comparison
  easier than angle comparison, especially beyond 2-3 categories.
- **Decomposition tree:** considered for Page 5 (seller risk drivers)
  but dropped — with only 3 dimensions (product, seller, geography) and
  no deep hierarchy, it would add interaction cost without revealing
  anything the scatter plot doesn't already show.
- **Gauge charts:** considered for Late Delivery Rate on Page 1 —
  dropped in favor of a plain KPI card; a gauge implies a defined
  target/threshold that this project hasn't set (no SLA data exists in
  the source).
