CREATE OR REFRESH MATERIALIZED VIEW `03_gold`.mv_revenue_daily
COMMENT 'Daily revenue and order metrics for executive reporting'
AS
SELECT
  d.full_date,
  d.year,
  d.quarter,
  d.month,
  d.month_name,
  d.is_weekend,
  COUNT(DISTINCT f.order_id)        AS order_count,
  COUNT(*)                          AS line_item_count,
  SUM(f.quantity)                   AS units_sold,
  ROUND(SUM(f.revenue), 2)          AS total_revenue,
  ROUND(AVG(f.revenue), 2)          AS avg_line_revenue
FROM `03_gold`.fct_sales f
INNER JOIN `03_gold`.dim_date d
  ON f.date_sk = d.date_sk
GROUP BY d.full_date, d.year, d.quarter, d.month, d.month_name, d.is_weekend;