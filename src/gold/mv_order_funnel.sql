CREATE OR REFRESH MATERIALIZED VIEW `03_gold`.mv_order_funnel
COMMENT 'Order counts and revenue by status for operational monitoring'
AS
SELECT
  o.order_status,
  COUNT(DISTINCT o.order_id)              AS order_count,
  ROUND(SUM(f.revenue), 2)                AS total_revenue,
  ROUND(AVG(f.revenue), 2)                AS avg_line_revenue
FROM `02_silver`.slv_orders o
LEFT JOIN `03_gold`.fct_sales f
  ON o.order_id = f.order_id
GROUP BY o.order_status
ORDER BY order_count DESC;