-- Business question: ¿Cómo evoluciona el revenue en el tiempo?
-- Restricted to the analysis window (see data_quality_notes.md #4).
-- Real result: steady growth from R$120,098.27 (Jan 2017) to a
-- R$1,003,862.14 peak in Nov 2017 (Black Friday, +52.06% MoM), pulling
-- back to R$742,183.79 in Dec (-26.07%), then stabilizing around
-- R$850k-1M/month through Aug 2018.
SELECT year_month, net_revenue, orders, avg_order_value, mom_revenue_growth_pct
FROM reporting.vw_monthly_revenue
ORDER BY month_start;
