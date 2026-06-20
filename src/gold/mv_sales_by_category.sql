CREATE OR REFRESH MATERIALIZED VIEW `03_gold`.mv_sales_by_category
COMMENT 'Sales metrics aggregated by product category'
AS
SELECT
  p.product_category,
  COUNT(DISTINCT f.order_id)              AS order_count,
  COUNT(DISTINCT f.product_sk)            AS distinct_products,
  SUM(f.quantity)                         AS units_sold,
  ROUND(SUM(f.revenue), 2)                AS total_revenue,
  ROUND(AVG(f.unit_price), 2)             AS avg_unit_price
FROM `03_gold`.fct_sales f
INNER JOIN `03_gold`.dim_product p
  ON f.product_sk = p.product_sk
GROUP BY p.product_category
ORDER BY total_revenue DESC;