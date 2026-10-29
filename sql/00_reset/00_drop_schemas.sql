-- ============================================================================
-- 00_drop_schemas.sql
-- Makes a full rebuild idempotent. Without this, a second run fails twice:
--   - CREATE TABLE raw.* errors because the tables already exist, and
--     \copy would append duplicate rows (rejected by the raw primary keys);
--   - DROP TABLE analytics.dim_* errors because the fact tables' foreign
--     keys and the reporting views depend on them.
-- Dropping the four pipeline schemas (and nothing else) in reverse
-- dependency order gives every later script a clean slate.
--
-- DESTRUCTIVE: removes every object in raw/staging/analytics/reporting.
-- Only run it as the first step of a full rebuild.
-- ============================================================================

DROP SCHEMA IF EXISTS reporting CASCADE;
DROP SCHEMA IF EXISTS analytics CASCADE;
DROP SCHEMA IF EXISTS staging   CASCADE;
DROP SCHEMA IF EXISTS raw       CASCADE;
