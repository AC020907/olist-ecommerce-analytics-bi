-- ============================================================================
-- 02_staging_geolocation.sql
-- raw.geolocation has 1,000,163 rows for only 19,015 distinct zip prefixes,
-- with multiple slightly different lat/lng samples per prefix, a trailing-
-- space city value found during profiling (e.g. 'salvador ' vs 'salvador'),
-- and 8 prefixes (out of 19,015 -- negligible, but not ignored) that map
-- to more than one state in the raw data.
--
-- This aggregates to exactly one row per zip prefix:
--   - lat/lng: simple average of all samples for that prefix.
--   - city/state: the most frequent (mode) value for that prefix, after
--     normalizing whitespace/case, so a tie or a rare bad sample doesn't
--     win by alphabetical accident.
--
-- Materialized as a TABLE (not a view) because it aggregates 1M rows and
-- is joined twice downstream (dim_customer, dim_seller) in Phase 5 --
-- recomputing it on every query would be wasteful.
-- ============================================================================

DROP TABLE IF EXISTS staging.geolocation_by_zip;

CREATE TABLE staging.geolocation_by_zip AS
WITH normalized AS (
    SELECT
        geolocation_zip_code_prefix                    AS zip_code_prefix,
        geolocation_lat                                  AS lat,
        geolocation_lng                                    AS lng,
        LOWER(TRIM(geolocation_city))                        AS city,
        geolocation_state                                      AS state
    FROM raw.geolocation
),
city_counts AS (
    SELECT zip_code_prefix, city, COUNT(*) AS n
    FROM normalized
    GROUP BY zip_code_prefix, city
),
city_mode AS (
    SELECT DISTINCT ON (zip_code_prefix) zip_code_prefix, city
    FROM city_counts
    ORDER BY zip_code_prefix, n DESC, city  -- deterministic tie-break
),
state_counts AS (
    SELECT zip_code_prefix, state, COUNT(*) AS n
    FROM normalized
    GROUP BY zip_code_prefix, state
),
state_mode AS (
    SELECT DISTINCT ON (zip_code_prefix) zip_code_prefix, state
    FROM state_counts
    ORDER BY zip_code_prefix, n DESC, state
),
coords AS (
    SELECT zip_code_prefix, AVG(lat) AS avg_lat, AVG(lng) AS avg_lng
    FROM normalized
    GROUP BY zip_code_prefix
)
SELECT
    co.zip_code_prefix,
    co.avg_lat,
    co.avg_lng,
    cm.city,
    sm.state
FROM coords co
JOIN city_mode cm  USING (zip_code_prefix)
JOIN state_mode sm USING (zip_code_prefix);

ALTER TABLE staging.geolocation_by_zip ADD PRIMARY KEY (zip_code_prefix);

COMMENT ON TABLE staging.geolocation_by_zip IS
'One row per zip_code_prefix: average lat/lng and the most frequent city/state from raw.geolocation. Rebuild by re-running this script if raw.geolocation changes.';
