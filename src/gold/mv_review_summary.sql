CREATE OR REFRESH MATERIALIZED VIEW `03_gold`.mv_review_summary
COMMENT 'Review score distribution and engagement metrics for operational monitoring'
AS
SELECT
  score,
  COUNT(*)                                            AS review_count,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)  AS pct_of_reviews,
  SUM(CASE WHEN verified THEN 1 ELSE 0 END)           AS verified_count,
  ROUND(AVG(helpful_votes), 1)                        AS avg_helpful_votes,
  COUNT(comment)                                      AS reviews_with_comment
FROM `02_silver`.slv_reviews
GROUP BY score
ORDER BY score DESC;