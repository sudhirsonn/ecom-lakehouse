CREATE OR REFRESH MATERIALIZED VIEW `03_gold`.dim_product
COMMENT 'Product dimension (SCD Type 1 — current values, surrogate key)'
AS
SELECT
  -- surrogate key: stable hash of the business key
  xxhash64(product_id)        AS product_sk,
  product_id,                 -- business/natural key
  product_category,
  product_name,
  base_price,
  weight_grams
FROM `02_silver`.slv_products

UNION ALL

-- Unknown member: catches facts whose product was filtered out by DQ rules
SELECT
  CAST(-1 AS BIGINT)    AS product_sk,
  'UNKNOWN'             AS product_id,
  'unknown'             AS product_category,
  'Unknown Product'     AS product_name,
  CAST(NULL AS DOUBLE)  AS base_price,
  CAST(NULL AS INT)     AS weight_grams;