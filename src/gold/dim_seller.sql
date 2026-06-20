CREATE OR REFRESH MATERIALIZED VIEW `03_gold`.dim_seller
COMMENT 'Seller dimension (SCD Type 1 — current values, surrogate key)'
AS
SELECT
  xxhash64(seller_id)         AS seller_sk,   -- surrogate key (hash of business key)
  seller_id,                                  -- business/natural key
  seller_name,
  seller_city,
  seller_state
FROM `02_silver`.slv_sellers;