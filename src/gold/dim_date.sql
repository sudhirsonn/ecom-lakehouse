CREATE OR REFRESH MATERIALIZED VIEW `03_gold`.dim_date
COMMENT 'Calendar dimension — one row per date with time attributes'
AS
WITH date_range AS (
  SELECT explode(sequence(
    DATE'2024-01-01',
    DATE'2027-12-31',
    INTERVAL 1 DAY
  )) AS date
)
SELECT
  CAST(date_format(date, 'yyyyMMdd') AS INT)  AS date_sk,      -- surrogate key (e.g. 20240115)
  date                                         AS full_date,
  YEAR(date)                                   AS year,
  QUARTER(date)                                AS quarter,
  MONTH(date)                                  AS month,
  date_format(date, 'MMMM')                    AS month_name,
  DAY(date)                                    AS day_of_month,
  date_format(date, 'EEEE')                    AS day_name,
  DAYOFWEEK(date)                              AS day_of_week,
  CASE WHEN DAYOFWEEK(date) IN (1, 7) THEN true ELSE false END AS is_weekend
FROM date_range;