-- ============================================================================
-- 01_create_schemas.sql
-- Separates the pipeline into schemas that mirror the repo's sql/ folders.
-- This is not decoration: it makes permissions and mental model explicit
-- (a BI tool should only ever read from `reporting`, never from `raw`).
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS raw;        -- 1:1 staging tables, one per CSV
CREATE SCHEMA IF NOT EXISTS staging;    -- cleaned/typed versions of raw (Phase 4)
CREATE SCHEMA IF NOT EXISTS analytics;  -- star schema: dims + facts (Phase 5)
CREATE SCHEMA IF NOT EXISTS reporting;  -- pre-aggregated views for Power BI (Phase 6)

COMMENT ON SCHEMA raw IS 'Unmodified load of the 9 Olist CSV files. No business logic here.';
COMMENT ON SCHEMA staging IS 'Typed, deduplicated, null-handled versions of raw tables.';
COMMENT ON SCHEMA analytics IS 'Star schema (dimensions + fact tables) consumed by SQL analysis and Power BI.';
COMMENT ON SCHEMA reporting IS 'Pre-aggregated views answering specific business questions.';
