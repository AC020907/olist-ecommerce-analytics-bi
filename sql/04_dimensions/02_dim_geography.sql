-- ============================================================================
-- 02_dim_geography.sql
-- Conformed geography dimension, keyed by zip_code_prefix, shared by both
-- dim_customer and dim_seller (a customer's and a seller's address are
-- the same *kind* of thing -- modeling them as two separate dimensions
-- would duplicate the state/region logic for no reason).
--
-- Adds a region column: Brazil's 27 states are too granular for an
-- executive-level chart, so we roll them up to the 5 official
-- geographic regions (Norte, Nordeste, Centro-Oeste, Sudeste, Sul).
-- ============================================================================

DROP TABLE IF EXISTS analytics.dim_geography;

CREATE TABLE analytics.dim_geography AS
SELECT
    g.zip_code_prefix,
    g.city,
    g.state,
    CASE g.state
        WHEN 'AC' THEN 'Norte'        WHEN 'AP' THEN 'Norte'
        WHEN 'AM' THEN 'Norte'        WHEN 'PA' THEN 'Norte'
        WHEN 'RO' THEN 'Norte'        WHEN 'RR' THEN 'Norte'
        WHEN 'TO' THEN 'Norte'
        WHEN 'AL' THEN 'Nordeste'     WHEN 'BA' THEN 'Nordeste'
        WHEN 'CE' THEN 'Nordeste'     WHEN 'MA' THEN 'Nordeste'
        WHEN 'PB' THEN 'Nordeste'     WHEN 'PE' THEN 'Nordeste'
        WHEN 'PI' THEN 'Nordeste'     WHEN 'RN' THEN 'Nordeste'
        WHEN 'SE' THEN 'Nordeste'
        WHEN 'DF' THEN 'Centro-Oeste' WHEN 'GO' THEN 'Centro-Oeste'
        WHEN 'MT' THEN 'Centro-Oeste' WHEN 'MS' THEN 'Centro-Oeste'
        WHEN 'ES' THEN 'Sudeste'      WHEN 'MG' THEN 'Sudeste'
        WHEN 'RJ' THEN 'Sudeste'      WHEN 'SP' THEN 'Sudeste'
        WHEN 'PR' THEN 'Sul'          WHEN 'RS' THEN 'Sul'
        WHEN 'SC' THEN 'Sul'
        ELSE 'unknown'
    END                          AS region,
    g.avg_lat,
    g.avg_lng
FROM staging.geolocation_by_zip g;

ALTER TABLE analytics.dim_geography ADD PRIMARY KEY (zip_code_prefix);

COMMENT ON TABLE analytics.dim_geography IS
'One row per zip_code_prefix (from staging.geolocation_by_zip), with Brazilian state rolled up to one of the 5 official regions. Shared/conformed dimension: both dim_customer and dim_seller join to this on zip_code_prefix.';
