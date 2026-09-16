# Star Schema Design

## Dimensions

| Dimension | Grain | Key | Source |
|---|---|---|---|
| `dim_date` | 1 row per calendar day (2016-09-01 to 2018-10-31) | `date_day` | generated |
| `dim_geography` | 1 row per zip code prefix | `zip_code_prefix` | `staging.geolocation_by_zip`, +region rollup |
| `dim_customer` | 1 row per **customer_unique_id** (real person) | `customer_unique_id` | `raw.customers` + `raw.orders` |
| `dim_seller` | 1 row per seller_id | `seller_id` | `raw.sellers` |
| `dim_product` | 1 row per product_id | `product_id` | `staging.products` |

`dim_geography` is a **conformed dimension**: both `dim_customer` and
`dim_seller` reference it via `zip_code_prefix`, so state/region logic
lives in exactly one place instead of being duplicated.

### Why natural keys, not surrogate integer keys

Every dimension here uses its natural business key (`customer_unique_id`,
`product_id`, etc.) as the primary key, not a generated surrogate integer.
This is a deliberate trade-off: surrogate keys exist mainly to handle
slowly-changing dimensions and to decouple the model from the source
system's key format. This is a static, historical, one-time-loaded
dataset (there's no daily refresh changing a customer's attributes over
time beyond what's already captured), and the natural keys are already
short fixed-length strings — so a surrogate key would add a join step
with no real benefit. In a live production system with SCD Type 2
requirements, I would introduce surrogate keys; documenting that
trade-off explicitly is part of defending this design.

### `dim_customer`: the most important modeling decision in this project

`customer_id` (in `raw.customers`) is **not a person** — Olist issues a
new one every time the same customer places a new order (verified,
profiling found 99,441 `customer_id` vs. 96,096 `customer_unique_id`). Building
`dim_customer` at `customer_id` grain would make repeat-purchase and
customer-value analysis meaningless. `dim_customer` is therefore built
at `customer_unique_id` grain, one row per real person.

A customer's city/state can change between orders (verified: 39 of
96,096 customers show more than one state across their orders, 122 more
than one city). `dim_customer` resolves this by taking the address from
the customer's **most recent** order — their current known profile —
using `ROW_NUMBER() OVER (PARTITION BY customer_unique_id ORDER BY
order_purchase_timestamp DESC)`. Verified on a real example: customer
`1f90117a847636892e3c5bf569f2ac68` ordered from Curitiba/PR in 2017-08
and later from Imbituba/SC in 2018-01 — `dim_customer` correctly shows
Imbituba/SC (the more recent order), not the first one.

## Fact tables — three, at three different grains, on purpose

| Fact | Grain | Row count | Use for |
|---|---|---|---|
| `fact_orders` | 1 row per order | 99,441 | Total Orders, AOV, delivery time, late rate, review score |
| `fact_order_items` | 1 row per order item | 112,650 | Revenue by product/category/seller |
| `fact_payments` | 1 row per payment transaction | 103,886 | Payment type / installments analysis |

### Why not one big fact table

`order_items` and `order_payments` fan out independently of each other:
9,803 orders have more than one item, 2,961 have more than one payment
row. Joining them directly at row level multiplies both. This is not
theoretical — I measured it:

**Demonstration (run against the real database):** for orders that have
*both* more than one item and more than one payment row, a naive
`order_items JOIN order_payments ON order_id` returns **1,622 rows** and
sums to **$142,553.18** in "revenue" for that subset. The correct
figure, from `fact_orders.items_revenue` for the same orders, is
**$54,422.37** across 275 orders — the naive join overstates revenue by
**2.6x** for just this slice of the data.

### How the design prevents it

`fact_orders` pre-aggregates `order_items` and `order_payments`
**independently**, each grouped to `order_id` first, before combining
them into one row per order:

```sql
items_agg    AS (SELECT order_id, COUNT(*) n_items, SUM(price) items_revenue,
                         SUM(freight_value) freight_total
                  FROM raw.order_items GROUP BY order_id),
payments_agg AS (SELECT order_id, SUM(payment_value) payments_total
                  FROM raw.order_payments GROUP BY order_id)
```

Neither subquery ever joins to the other at row level — they're combined
only after each has already been collapsed to one row per order. This is
the single technique that prevents the fan-out.

`fact_order_items` and `fact_payments` are kept as separate, ungrouped
facts at their native grain specifically so product/seller and
payment-method breakdowns remain possible — but the rule is: **never
join `fact_order_items` to `fact_payments` at row level.** If a report
needs both dimensions at once (e.g. "revenue by category AND by payment
type"), each is aggregated to the order grain independently and then
joined on `order_id` — the same pattern used inside `fact_orders`
itself.

### Revenue vs. payments: a real, explained reconciliation gap

`SUM(items_revenue + freight_total)` across all orders is $15,843,409.78;
`SUM(payments_total)` is $16,008,872.12 — a $165,462.34 gap (~1%).
Verified this is not a bug: **98.3% of the gap ($162,591.95)** comes from
773 orders with `order_status IN ('unavailable', 'canceled', 'created',
'invoiced', 'shipped')` that have **zero rows in `order_items`** (no
line-item ever got recorded, e.g. because the order was cancelled before
fulfillment) but **do** have a captured payment. This is documented as a
known, explained gap — not silently reconciled away.

## Grain safety checklist (for the interview)

- Is `fact_orders.items_revenue` consistent with summing `fact_order_items.price`
  directly? Yes — verified equal to the cent ($13,591,643.70 both ways).
- Can `fact_order_items` be joined to `fact_payments` for a combined report?
  No, not at row level — aggregate each to `order_id` first.
- Can `fact_orders` be joined to `dim_product`? No — product doesn't exist
  at order grain, only at order-item grain. Use `fact_order_items` for
  anything product-related.
- Does every fact row have a valid FK to every dimension it references?
  Yes — enforced by `FOREIGN KEY` constraints on all three fact tables;
  the load would have failed otherwise (and did not).
