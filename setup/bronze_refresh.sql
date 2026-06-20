-- Operational refresh of the 7 Bronze streaming tables (incremental).
-- Run as the job's first task before the Silver/Gold pipeline.
REFRESH STREAMING TABLE ${catalog}.`01_bronze`.br_customers;
REFRESH STREAMING TABLE ${catalog}.`01_bronze`.br_products;
REFRESH STREAMING TABLE ${catalog}.`01_bronze`.br_sellers;
REFRESH STREAMING TABLE ${catalog}.`01_bronze`.br_orders;
REFRESH STREAMING TABLE ${catalog}.`01_bronze`.br_order_items;
REFRESH STREAMING TABLE ${catalog}.`01_bronze`.br_payments;
REFRESH STREAMING TABLE ${catalog}.`01_bronze`.br_reviews;
