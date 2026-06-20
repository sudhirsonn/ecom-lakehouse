CREATE OR REFRESH MATERIALIZED VIEW `03_gold`.mv_sales_by_state
COMMENT 'Sales metrics aggregated by customer state for geographic analysis'
AS
SELECT
  c.state,
  COUNT(DISTINCT c.customer_id)      AS customer_count,
  COUNT(DISTINCT f.order_id)         AS order_count,
  SUM(f.quantity)                    AS units_sold,
  ROUND(SUM(f.revenue), 2)           AS total_revenue,
  ROUND(SUM(f.revenue) / COUNT(DISTINCT f.order_id), 2) AS avg_order_value
FROM `03_gold`.fct_sales f
INNER JOIN `03_gold`.dim_customer_keyed c
  ON f.customer_sk = c.customer_sk
GROUP BY c.state
ORDER BY total_revenue DESC;