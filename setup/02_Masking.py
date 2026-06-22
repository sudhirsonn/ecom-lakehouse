-- Databricks notebook source
-- MAGIC %md
-- MAGIC ### Step 1 — Create the masking function

-- COMMAND ----------

CREATE OR REPLACE FUNCTION ecom_dev.`03_gold`.mask_email(email STRING)
RETURNS STRING
COMMENT 'Redacts email unless the caller is in ecom_engineers'
RETURN
  CASE
    WHEN is_account_group_member('ecom_engineers') THEN email
    ELSE CONCAT(LEFT(email, 2), '***@***.***')
  END;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Step 2 — Apply the mask to the column

-- COMMAND ----------

ALTER TABLE ecom_dev.`03_gold`.dim_customer
ALTER COLUMN email SET MASK ecom_dev.`03_gold`.mask_email;

-- COMMAND ----------

ALTER MATERIALIZED VIEW ecom_dev.`03_gold`.dim_customer_keyed
ALTER COLUMN email SET MASK ecom_dev.`03_gold`.mask_email;

-- COMMAND ----------

SELECT is_account_group_member('ecom_analysts');

-- COMMAND ----------

DESCRIBE TABLE EXTENDED ecom_dev.`03_gold`.dim_customer;

-- COMMAND ----------

--SELECT customer_id, email FROM ecom_dev.`03_gold`.dim_customer LIMIT 5;
SELECT customer_id, email FROM ecom_dev.`03_gold`.dim_customer_keyed LIMIT 5;


-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Create the row filter function

-- COMMAND ----------

CREATE OR REPLACE FUNCTION ecom_dev.`03_gold`.filter_by_region(state STRING)
RETURNS BOOLEAN
COMMENT 'Restricts ecom_bi_reader to TX only; everyone else sees all rows'
RETURN
  is_account_group_member('ecom_engineers')
  OR is_account_group_member('ecom_analysts')
  OR (is_account_group_member('ecom_bi_reader') AND state = 'TX');

-- COMMAND ----------

ALTER MATERIALIZED VIEW ecom_dev.`03_gold`.mv_sales_by_state
SET ROW FILTER ecom_dev.`03_gold`.filter_by_region ON (state);

-- COMMAND ----------

SELECT * FROM ecom_dev.`03_gold`.mv_sales_by_state;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Tag the column -  ABAC

-- COMMAND ----------

--ALTER TABLE ecom_dev.`03_gold`.dim_customer
--SET TAGS ('sensitivity' = 'pii');

-- COMMAND ----------

ALTER TABLE ecom_dev.`03_gold`.dim_customer
ALTER COLUMN email SET TAGS ('sensitivity' = 'pii');

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Create a Function

-- COMMAND ----------

CREATE OR REPLACE FUNCTION ecom_dev.`03_gold`.mask_tagged_pii(value STRING)
RETURNS STRING
COMMENT 'Masks any column tagged sensitivity=pii unless caller is ecom_engineers'
RETURN
  CASE
    WHEN is_account_group_member('ecom_engineers') THEN value
    ELSE '***REDACTED-PII***'
  END;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Create a Policy

-- COMMAND ----------

CREATE OR REPLACE POLICY pii_email_policy
ON TABLE ecom_dev.`03_gold`.dim_customer
COMMENT 'Masks any column tagged sensitivity=pii unless caller is ecom_engineers'
COLUMN MASK ecom_dev.`03_gold`.mask_tagged_pii
TO `account users`
EXCEPT `ecom_engineers`
FOR TABLES
MATCH COLUMNS has_tag_value('sensitivity', 'pii') AS pii_col
ON COLUMN pii_col;

-- COMMAND ----------

SELECT * FROM system.information_schema.column_tags
WHERE catalog_name = 'ecom_dev' AND schema_name = '03_gold' AND table_name = 'dim_customer';

-- COMMAND ----------

SELECT customer_id, email FROM ecom_dev.`03_gold`.dim_customer LIMIT 5;