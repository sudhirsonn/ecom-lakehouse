-- Databricks notebook source
-- MAGIC %md
-- MAGIC ### ecom_engineers: full access across all layers

-- COMMAND ----------

GRANT USE CATALOG ON CATALOG ecom_dev TO `ecom_engineers`;
GRANT USE SCHEMA ON SCHEMA ecom_dev.`01_bronze` TO `ecom_engineers`;
GRANT USE SCHEMA ON SCHEMA ecom_dev.`02_silver` TO `ecom_engineers`;
GRANT USE SCHEMA ON SCHEMA ecom_dev.`03_gold`   TO `ecom_engineers`;
GRANT ALL PRIVILEGES ON SCHEMA ecom_dev.`01_bronze` TO `ecom_engineers`;
GRANT ALL PRIVILEGES ON SCHEMA ecom_dev.`02_silver` TO `ecom_engineers`;
GRANT ALL PRIVILEGES ON SCHEMA ecom_dev.`03_gold`   TO `ecom_engineers`;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### ecom_analysts: read-only, Gold layer only

-- COMMAND ----------

GRANT USE CATALOG ON CATALOG ecom_dev TO `ecom_analysts`;
GRANT USE SCHEMA ON SCHEMA ecom_dev.`03_gold` TO `ecom_analysts`;
GRANT SELECT ON SCHEMA ecom_dev.`03_gold` TO `ecom_analysts`;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### ecom_bi_reader: read-only, Gold layer only 
-- MAGIC (same base as analysts; row filter applied separately below narrows what they actually see)
-- MAGIC

-- COMMAND ----------

GRANT USE CATALOG ON CATALOG ecom_dev TO `ecom_bi_reader`;
GRANT USE SCHEMA ON SCHEMA ecom_dev.`03_gold` TO `ecom_bi_reader`;
GRANT SELECT ON SCHEMA ecom_dev.`03_gold` TO `ecom_bi_reader`;

-- COMMAND ----------

SHOW GRANTS ON SCHEMA ecom_dev.`03_gold`;