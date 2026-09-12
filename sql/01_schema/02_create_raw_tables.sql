-- ============================================================================
-- 02_create_raw_tables.sql
-- Staging tables, one per Olist CSV, with correct types (not everything
-- VARCHAR) and PK/FK/CHECK constraints based on what we verified in Phase 1
-- profiling (see docs/data_quality_notes.md).
--
-- Type decisions worth calling out:
--   - All Olist ids (customer_id, order_id, product_id, seller_id,
--     review_id, customer_unique_id) are 32-char hex strings -> CHAR(32),
--     not a generic VARCHAR, since the length is fixed and verified.
--   - zip_code_prefix is CHAR(5), NOT INTEGER. 23,995 of 99,441 customer
--     zip prefixes start with '0' (e.g. '01037' in Sao Paulo). Storing
--     this as INTEGER silently truncates the leading zero and corrupts
--     the value. This is exactly the kind of wrong-type mistake the
--     project explicitly wants to avoid.
--   - state codes are CHAR(2) (Brazilian UF codes: SP, RJ, ...).
--   - free-text review fields are TEXT (length is unpredictable and
--     Postgres has no performance penalty for TEXT vs VARCHAR(n)).
--   - money/measurement columns are NUMERIC, never FLOAT, to avoid
--     floating-point rounding on prices and freight values.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- Independent tables (no FK dependencies)
-- ---------------------------------------------------------------------------

CREATE TABLE raw.customers (
    customer_id                CHAR(32)    NOT NULL,
    customer_unique_id         CHAR(32)    NOT NULL,
    customer_zip_code_prefix   CHAR(5)     NOT NULL,
    customer_city              VARCHAR(100) NOT NULL,
    customer_state             CHAR(2)     NOT NULL,
    CONSTRAINT pk_customers PRIMARY KEY (customer_id)
);
COMMENT ON TABLE raw.customers IS 'One row per customer_id (order-level identifier, NOT per person). Use customer_unique_id for real customer identity.';

CREATE TABLE raw.products (
    product_id                     CHAR(32)     NOT NULL,
    product_category_name          VARCHAR(100),  -- nullable: 610 products have no category (verified)
    product_name_lenght             SMALLINT,
    product_description_lenght      INTEGER,
    product_photos_qty              SMALLINT,
    product_weight_g                INTEGER,
    product_length_cm               INTEGER,
    product_height_cm               INTEGER,
    product_width_cm                INTEGER,
    CONSTRAINT pk_products PRIMARY KEY (product_id)
);
COMMENT ON TABLE raw.products IS 'One row per product. product_category_name is in Portuguese; join to product_category_name_translation for English.';

CREATE TABLE raw.sellers (
    seller_id                CHAR(32)    NOT NULL,
    seller_zip_code_prefix   CHAR(5)     NOT NULL,
    seller_city              VARCHAR(100) NOT NULL,
    seller_state             CHAR(2)     NOT NULL,
    CONSTRAINT pk_sellers PRIMARY KEY (seller_id)
);

CREATE TABLE raw.product_category_name_translation (
    product_category_name          VARCHAR(100) NOT NULL,
    product_category_name_english  VARCHAR(100) NOT NULL,
    CONSTRAINT pk_category_translation PRIMARY KEY (product_category_name)
);

CREATE TABLE raw.geolocation (
    geolocation_zip_code_prefix  CHAR(5)         NOT NULL,
    geolocation_lat               NUMERIC(10, 7) NOT NULL,
    geolocation_lng               NUMERIC(10, 7) NOT NULL,
    geolocation_city              VARCHAR(100)   NOT NULL,
    geolocation_state             CHAR(2)        NOT NULL
    -- No PK: verified this table has many rows per zip prefix with no
    -- unique key as distributed. It is aggregated in the staging layer.
);
COMMENT ON TABLE raw.geolocation IS 'Multiple lat/lng samples per zip prefix, no unique key. Aggregated to one row per prefix in staging (Phase 4).';

-- ---------------------------------------------------------------------------
-- orders: depends on customers
-- ---------------------------------------------------------------------------

CREATE TABLE raw.orders (
    order_id                        CHAR(32)    NOT NULL,
    customer_id                     CHAR(32)    NOT NULL,
    order_status                    VARCHAR(20) NOT NULL,
    order_purchase_timestamp        TIMESTAMP   NOT NULL,
    order_approved_at               TIMESTAMP,              -- nullable: not yet approved / canceled
    order_delivered_carrier_date    TIMESTAMP,              -- nullable: not yet shipped
    order_delivered_customer_date   TIMESTAMP,              -- nullable: not yet delivered
    order_estimated_delivery_date   TIMESTAMP   NOT NULL,
    CONSTRAINT pk_orders PRIMARY KEY (order_id),
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id)
        REFERENCES raw.customers (customer_id),
    CONSTRAINT chk_orders_status CHECK (
        order_status IN ('created', 'approved', 'processing', 'invoiced',
                          'shipped', 'delivered', 'canceled', 'unavailable')
    )
);
CREATE INDEX ix_orders_customer_id ON raw.orders (customer_id);
CREATE INDEX ix_orders_purchase_ts ON raw.orders (order_purchase_timestamp);

-- ---------------------------------------------------------------------------
-- order_items: depends on orders, products, sellers
-- ---------------------------------------------------------------------------

CREATE TABLE raw.order_items (
    order_id              CHAR(32)      NOT NULL,
    order_item_id          SMALLINT      NOT NULL,
    product_id             CHAR(32)      NOT NULL,
    seller_id               CHAR(32)      NOT NULL,
    shipping_limit_date      TIMESTAMP     NOT NULL,
    price                    NUMERIC(10,2) NOT NULL,
    freight_value            NUMERIC(10,2) NOT NULL,
    CONSTRAINT pk_order_items PRIMARY KEY (order_id, order_item_id),
    CONSTRAINT fk_order_items_order FOREIGN KEY (order_id)
        REFERENCES raw.orders (order_id),
    CONSTRAINT fk_order_items_product FOREIGN KEY (product_id)
        REFERENCES raw.products (product_id),
    CONSTRAINT fk_order_items_seller FOREIGN KEY (seller_id)
        REFERENCES raw.sellers (seller_id),
    CONSTRAINT chk_order_items_price CHECK (price >= 0),
    CONSTRAINT chk_order_items_freight CHECK (freight_value >= 0)
);
COMMENT ON TABLE raw.order_items IS 'Grain: one row per item within an order. An order with N items has N rows here.';
CREATE INDEX ix_order_items_product_id ON raw.order_items (product_id);
CREATE INDEX ix_order_items_seller_id ON raw.order_items (seller_id);

-- ---------------------------------------------------------------------------
-- order_payments: depends on orders
-- ---------------------------------------------------------------------------

CREATE TABLE raw.order_payments (
    order_id                CHAR(32)      NOT NULL,
    payment_sequential       SMALLINT      NOT NULL,
    payment_type              VARCHAR(20)   NOT NULL,
    payment_installments      SMALLINT      NOT NULL,
    payment_value              NUMERIC(10,2) NOT NULL,
    CONSTRAINT pk_order_payments PRIMARY KEY (order_id, payment_sequential),
    CONSTRAINT fk_order_payments_order FOREIGN KEY (order_id)
        REFERENCES raw.orders (order_id),
    CONSTRAINT chk_order_payments_installments CHECK (payment_installments >= 0),
    CONSTRAINT chk_order_payments_value CHECK (payment_value >= 0)
);
COMMENT ON TABLE raw.order_payments IS 'Grain: one row per payment transaction within an order. An order can have multiple payment rows (split payments).';

-- ---------------------------------------------------------------------------
-- order_reviews: depends on orders
-- NOTE: verified that review_id is NOT unique on its own (789 review_id
-- values are reused across different order_id values -- an Olist data
-- quirk, not a data entry duplicate: 0 duplicate rows on the full row,
-- and 0 duplicates on (review_id, order_id)). PK is therefore composite.
-- ---------------------------------------------------------------------------

CREATE TABLE raw.order_reviews (
    review_id                  CHAR(32)    NOT NULL,
    order_id                    CHAR(32)    NOT NULL,
    review_score                  SMALLINT    NOT NULL,
    review_comment_title           TEXT,
    review_comment_message          TEXT,
    review_creation_date              TIMESTAMP NOT NULL,
    review_answer_timestamp            TIMESTAMP NOT NULL,
    CONSTRAINT pk_order_reviews PRIMARY KEY (review_id, order_id),
    CONSTRAINT fk_order_reviews_order FOREIGN KEY (order_id)
        REFERENCES raw.orders (order_id),
    CONSTRAINT chk_order_reviews_score CHECK (review_score BETWEEN 1 AND 5)
);
COMMENT ON TABLE raw.order_reviews IS 'review_id alone is not unique (reused ~789 times across different orders in the source data) -- PK is (review_id, order_id).';
CREATE INDEX ix_order_reviews_order_id ON raw.order_reviews (order_id);
