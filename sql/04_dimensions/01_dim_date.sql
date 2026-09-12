-- ============================================================================
-- 01_dim_date.sql
-- Standard calendar dimension. Grain: one row per calendar day.
-- Uses the DATE itself as the primary key (not a surrogate integer) --
-- for a static, historical dataset like this one there's no benefit to
-- an int surrogate, and DATE keys join cleanly to Power BI's own
-- auto date handling if ever needed.
--
-- Spans the full order range (2016-09-04 to 2018-10-17) plus a small
-- buffer, and flags is_in_analysis_window per data_quality_notes.md #4:
-- 2016 and 2018-09/10 are truncated edges of the dataset, not real
-- seasonality, so trend charts should filter to this window.
-- ============================================================================

DROP TABLE IF EXISTS analytics.dim_date;

CREATE TABLE analytics.dim_date AS
SELECT
    d::date                                              AS date_day,
    EXTRACT(YEAR FROM d)::int                              AS year,
    EXTRACT(QUARTER FROM d)::int                             AS quarter,
    EXTRACT(MONTH FROM d)::int                                 AS month,
    TO_CHAR(d, 'Month')                                          AS month_name,
    TO_CHAR(d, 'Mon')                                              AS month_short_name,
    TO_CHAR(d, 'YYYY-MM')                                            AS year_month,
    EXTRACT(DAY FROM d)::int                                           AS day_of_month,
    EXTRACT(ISODOW FROM d)::int                                          AS day_of_week,   -- 1=Mon .. 7=Sun
    TO_CHAR(d, 'Day')                                                     AS day_name,
    (EXTRACT(ISODOW FROM d) IN (6, 7))                                     AS is_weekend,
    (d BETWEEN DATE '2017-01-01' AND DATE '2018-08-31')                     AS is_in_analysis_window
FROM generate_series(DATE '2016-09-01', DATE '2018-10-31', INTERVAL '1 day') AS d;

ALTER TABLE analytics.dim_date ADD PRIMARY KEY (date_day);

COMMENT ON TABLE analytics.dim_date IS
'One row per calendar day, 2016-09-01 to 2018-10-31. is_in_analysis_window = true for 2017-01 to 2018-08, the window with complete monthly data (see data_quality_notes.md #4).';
