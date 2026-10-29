# I Will Build a Professional Power BI Sales Dashboard with SQL and Python

## Short description (catalog card)

Turn your sales exports into a reliable, automated dashboard: cleaned and validated data, clear KPI definitions, and a Power BI report your team can use every week.

## Description

Most sales reports break in the same places: revenue that changes depending on who built the spreadsheet, orders counted twice because they had several items or payments, canceled sales mixed with real ones, and a dashboard that someone has to rebuild by hand every month.

I build sales dashboards on top of a clean data model, not on top of raw exports. I load your data (Excel/CSV exports, a database, or your e-commerce platform's exports), clean it, model it so the numbers add up, check it with automated tests, and deliver a Power BI dashboard with the KPIs you actually use to run the business.

You can see the full approach in my public case study — a 1.5-million-row e-commerce dataset turned into a PostgreSQL star schema, 44 automated data-quality checks, a six-page Power BI dashboard and a browser-based demo:

- Code and documentation: https://github.com/AC020907/olist-ecommerce-analytics-bi
- Case study: docs/CASE_STUDY.md in that repository

## Problems I solve

- "Our revenue number is different in every report."
- "We spend hours every week copying exports into Excel."
- "We know sales are up or down, but not which products, regions or sellers explain it."
- "We have delivery or fulfillment problems but can't see where they are or what they cost us."
- "We bought Power BI, but nobody has built anything useful with it yet."

## What you get

- A Power BI report (.pbix) with an executive overview and the pages agreed in scope (e.g. sales trends, products/categories, customers, regions, sales reps or sellers, operations).
- A documented data model (star schema) — revenue never double-counts.
- KPI definitions written down in plain language (what counts as revenue, an order, a returning customer, a late delivery…).
- Data-quality checks that flag problems in your source data before they reach the dashboard.
- For Standard/Premium: SQL and/or Python transformations you own, and a refresh process.
- A walkthrough call or recorded video explaining how to use and refresh the dashboard.

## Tools

Power BI (Power Query, DAX), SQL (PostgreSQL; I can adapt to SQL Server or MySQL), Python (pandas, psycopg, pytest), Excel/CSV, Git. Optional: a web version of the dashboard in Streamlit for people without Power BI licences.

## What I need from you

- Sample or full exports of the data (or read-only database access), with a short description of each file.
- The 5–10 questions or KPIs that matter most to you.
- One contact who can answer questions about how your business records sales, returns and cancellations.
- Your Power BI setup (Desktop only, Power BI Service / Pro licences) if the report must be published.

## How I work

1. **Discovery (30 min call or questionnaire).** Your goals, data sources, KPIs and users.
2. **Data review (1–2 days).** I profile your data and send a short note on quality issues and the KPI definitions I propose. Nothing is built before we agree on the definitions.
3. **Model and validation.** Cleaning, star schema, automated checks; I reconcile totals against a number you already trust (e.g. your accounting monthly revenue).
4. **Dashboard.** A first version for feedback, then revisions included in your package.
5. **Handover.** Files, documentation and a walkthrough. You own everything.

## FAQ

**Do you need access to my systems?**
No. Exports are enough to start. Read-only access is only needed if you want automated refresh from a database.

**Can you work with Excel files instead of a database?**
Yes. Basic is built directly from clean Excel/CSV files. Standard and Premium add a transformation layer so new exports can be dropped in and refreshed.

**Will the dashboard refresh automatically?**
Scheduled refresh needs Power BI Service (Pro or Premium licences, paid to Microsoft) and, for on-premise data, a gateway. I can set it up if you have them, or deliver a one-click manual refresh if you don't.

**How do I know the numbers are right?**
Every package includes a reconciliation step against a total you already trust, and Standard/Premium include automated data-quality checks that run on every refresh.

**Is my data safe?**
I work only with the data you share, on my own machine or in your environment, never share it with third parties and delete it at the end of the project on request. I am happy to sign an NDA.

**Do you have previous Upwork clients?**
I am new to Upwork. My public case study shows the full process end to end so you can judge the quality before hiring; I am happy to start with a small, fixed-price Basic package.

## Scope limits

- Data that cannot be exported or accessed (e.g. no API/export available) is out of scope until access is solved.
- Power BI licences, gateways and cloud costs are paid directly by the client.
- Predictive models, forecasting and machine learning are not included (available as a separate quote).
- Large data-entry or manual cleanup of free text is not included.
- Changes to agreed KPI definitions after the model is built count as new scope.

## Support and maintenance (optional)

- **Bug-fix warranty:** 14 days after delivery for anything that does not work as agreed — included.
- **Monthly care plan:** monitoring of refreshes and data-quality checks, small changes (new measure, new filter, layout tweaks) up to 4 hours/month.
- **Hourly:** larger changes or new pages billed per hour after a short estimate.
