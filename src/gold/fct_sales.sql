CREATE OR REFRESH MATERIALIZED VIEW `03_gold`.fct_sales
COMMENT 'Sales fact — one row per order line item, with measures and dimension keys'
AS
SELECT
  oi.order_id,
  oi.item_seq,
  c.customer_sk,
  COALESCE(p.product_sk, -1)  AS product_sk,
  s.seller_sk,
  d.date_sk,
  oi.quantity,
  CASE WHEN oi.unit_price > 0 THEN oi.unit_price END AS unit_price,
  ROUND(CASE WHEN oi.unit_price > 0 THEN oi.quantity * oi.unit_price END, 2) AS revenue,
  o.order_status
FROM `02_silver`.slv_order_items oi
INNER JOIN `02_silver`.slv_orders o
  ON oi.order_id = o.order_id
LEFT JOIN `03_gold`.dim_customer_keyed c
  ON o.customer_id = c.customer_id AND c.is_current = true   -- current version
LEFT JOIN `03_gold`.dim_product p
  ON oi.product_id = p.product_id
LEFT JOIN `03_gold`.dim_seller s
  ON oi.seller_id = s.seller_id
LEFT JOIN `03_gold`.dim_date d
  ON CAST(date_format(o.order_ts, 'yyyyMMdd') AS INT) = d.date_sk;