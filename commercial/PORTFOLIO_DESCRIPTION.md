# Upwork Portfolio Entry

**Title:** E-Commerce Sales Analytics & BI Dashboard (Power BI, SQL, Python)

**Role:** Sole developer — data engineering, modeling, validation, dashboard design.

**Skills to tag:** Microsoft Power BI · SQL · PostgreSQL · Python · Data Modeling · ETL · Dashboard · Data Visualization · DAX · Business Intelligence

**Images (in this order):** `images/demo/01_executive_overview.png`, `images/demo/03_delivery_satisfaction.png`, `images/Executive_overview.png`, `images/demo/05_methodology_data_quality.png`.

---

## Short version (~600 characters)

End-to-end sales analytics on a public e-commerce dataset (99k orders, 1.5M rows). I built a PostgreSQL warehouse with a Python pipeline, a star schema that prevents double-counted revenue, 44 automated data-quality checks, a 6-page Power BI dashboard and a browser-based demo. The analysis showed late deliveries average 2.27/5 in reviews versus 4.29/5 on time, and identified 41 high-volume sellers with both poor delivery and low ratings. Independent portfolio project on public Olist data.

## Extended version

**Challenge.** A multi-seller marketplace stores orders, items, payments, reviews, sellers, products and locations in separate tables. Joined naively, multi-item and multi-payment orders double-count revenue, canceled orders inflate sales and every order looks like a new customer.

**What I built.**
- A PostgreSQL warehouse (raw → staging → analytics → reporting) loaded and rebuilt by a Python pipeline in one command (~30 s).
- A star schema with order-, item- and payment-level fact tables so revenue is never multiplied by joins.
- 44 automated checks: unique keys, referential integrity, dates, money, and revenue reconciliation across every table and view — gross revenue matches the source to the cent.
- A six-page Power BI dashboard and a web demo with filters and a weekly KPI scorecard.

**Results of the analysis (public data, not a client outcome).**
- R$13.49M net revenue across 98,207 valid orders; +138% year-over-year (Jan–Aug).
- On-time orders: 4.29/5 average review; late orders: 2.27/5.
- Late-delivery rate jumped from ~3% to 12–19% in peak months.
- Top 10% of sellers generate 67% of revenue; 41 high-volume sellers combine poor delivery and low ratings.

**What it means for your business.** The same pipeline works with your exports: one trusted revenue number, a dashboard that refreshes instead of being rebuilt, and early warnings on delivery and customer satisfaction.

Live app: https://olist-sales-analytics.streamlit.app
Code and documentation: https://github.com/AC020907/olist-ecommerce-analytics-bi
