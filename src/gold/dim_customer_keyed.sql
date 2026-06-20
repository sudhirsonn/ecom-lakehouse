CREATE OR REFRESH MATERIALIZED VIEW `03_gold`.dim_customer_keyed
COMMENT 'Customer dimension presentation: adds per-version surrogate key, friendly validity columns'
AS
SELECT
  -- per-version surrogate key: business key + version start = unique per version
  xxhash64(customer_id, `__START_AT`)  AS customer_sk,
  customer_id,                          
  customer_name,
  email,
  city,
  state,
  signup_ts,
  `__START_AT`                          AS valid_from,
  `__END_AT`                            AS valid_to,
  CASE WHEN `__END_AT` IS NULL THEN true ELSE false END AS is_current
FROM `03_gold`.dim_customer;