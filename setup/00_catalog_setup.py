-- Databricks notebook source
-- MAGIC %md
-- MAGIC ### 1. External location: the raw landing zone.
-- MAGIC Bronze Auto Loader reads files from here (via a volume).

-- COMMAND ----------


CREATE EXTERNAL LOCATION IF NOT EXISTS ecom_landing_dev
URL 'abfss://landing@ecomlakehousedev.dfs.core.windows.net/'
WITH (STORAGE CREDENTIAL ecom_mi)
COMMENT 'Raw file landing zone (dev)';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### It means storage credential, the managed identity, and the role assignment are all wired correctly and Unity Catalog can reach the storage.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### 2. External location: catalog-level managed storage (for dev).
-- MAGIC ecom_dev managed tables/volumes physically live here.  
-- MAGIC Catalog-level managed storage = the recommended isolation pattern.  
-- MAGIC New auto-enabled metastores have no metastore-level managed storage, so I assigned managed storage at the catalog level — which is also the recommended pattern for per-environment data isolation.

-- COMMAND ----------

CREATE EXTERNAL LOCATION IF NOT EXISTS ecom_managed_dev
URL 'abfss://metastore-root@ecomlakehousedev.dfs.core.windows.net/dev/'
WITH (STORAGE CREDENTIAL ecom_mi)
COMMENT 'Managed storage root for the ecom_dev catalog'

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### 3.The dev catalog, with its own managed storage location.

-- COMMAND ----------

CREATE CATALOG IF NOT EXISTS ecom_dev
  MANAGED LOCATION 'abfss://metastore-root@ecomlakehousedev.dfs.core.windows.net/dev/'
  COMMENT 'E-commerce lakehouse — dev environment';

-- COMMAND ----------

USE CATALOG ecom_dev;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### 4. Medallion schemas. Numeric prefixes sort them in layer order.

-- COMMAND ----------

CREATE SCHEMA IF NOT EXISTS 01_bronze
COMMENT 'Raw data landing zone - minimal transformation';

CREATE SCHEMA IF NOT EXISTS 02_silver
COMMENT 'Cleansed, conformed, deduplicated, validated data';

CREATE SCHEMA IF NOT EXISTS 03_gold
COMMENT 'Aggregated, summarized, dimensional model + materialized views for BI';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### 5. Create Volume

-- COMMAND ----------

CREATE EXTERNAL VOLUME IF NOT EXISTS ecom_dev.`01_bronze`.raw_landing
  LOCATION 'abfss://landing@ecomlakehousedev.dfs.core.windows.net/dev/'
  COMMENT 'External volume over the ADLS gen2 landing zone dev landing zone';            

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### 6. Create Checkpoint

-- COMMAND ----------

CREATE VOLUME IF NOT EXISTS 01_bronze._checkpoints
COMMENT 'Managed volume for Auto Loader / streaming checkpoints';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### 7. Verify

-- COMMAND ----------

SHOW SCHEMAS IN ecom_dev;

-- COMMAND ----------

SHOW VOLUMES IN ecom_dev.`01_bronze`;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### 8. External location: catalog-level managed storage (for test & prod).

-- COMMAND ----------

CREATE EXTERNAL LOCATION IF NOT EXISTS ecom_managed_test
  URL 'abfss://metastore-root@ecomlakehousedev.dfs.core.windows.net/test/'
  WITH (STORAGE CREDENTIAL ecom_mi);

CREATE EXTERNAL LOCATION IF NOT EXISTS ecom_managed_prod
  URL 'abfss://metastore-root@ecomlakehousedev.dfs.core.windows.net/prod/'
  WITH (STORAGE CREDENTIAL ecom_mi);

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### 9.Create the test & prod catalog, with its own managed storage location.

-- COMMAND ----------

CREATE CATALOG IF NOT EXISTS ecom_test
  MANAGED LOCATION 'abfss://metastore-root@ecomlakehousedev.dfs.core.windows.net/test/'
  COMMENT 'E-commerce lakehouse — test environment';

CREATE CATALOG IF NOT EXISTS ecom_prod
  MANAGED LOCATION 'abfss://metastore-root@ecomlakehousedev.dfs.core.windows.net/prod/'
  COMMENT 'E-commerce lakehouse — prod environment';

-- COMMAND ----------

USE CATALOG ecom_test;
CREATE SCHEMA IF NOT EXISTS `01_bronze` COMMENT 'Raw ingested data (Auto Loader)';
CREATE SCHEMA IF NOT EXISTS `02_silver` COMMENT 'Cleansed, conformed, validated data';
CREATE SCHEMA IF NOT EXISTS `03_gold`   COMMENT 'Star schema + materialized views for BI';

-- COMMAND ----------

CREATE EXTERNAL VOLUME IF NOT EXISTS ecom_test.`01_bronze`.raw_landing
  LOCATION 'abfss://landing@ecomlakehousedev.dfs.core.windows.net/test/'
  COMMENT 'External volume over the test landing zone';
CREATE VOLUME IF NOT EXISTS ecom_test.`01_bronze`._checkpoints
  COMMENT 'Managed volume for checkpoints (test)';

-- COMMAND ----------

USE CATALOG ecom_prod;
CREATE SCHEMA IF NOT EXISTS `01_bronze` COMMENT 'Raw ingested data (Auto Loader)';
CREATE SCHEMA IF NOT EXISTS `02_silver` COMMENT 'Cleansed, conformed, validated data';
CREATE SCHEMA IF NOT EXISTS `03_gold`   COMMENT 'Star schema + materialized views for BI';

-- COMMAND ----------

-- PROD landing volume → landing/prod/
CREATE EXTERNAL VOLUME IF NOT EXISTS ecom_prod.`01_bronze`.raw_landing
  LOCATION 'abfss://landing@ecomlakehousedev.dfs.core.windows.net/prod/'
  COMMENT 'External volume over the prod landing zone';

-- PROD managed checkpoints volume
CREATE VOLUME IF NOT EXISTS ecom_prod.`01_bronze`._checkpoints
  COMMENT 'Managed volume for Auto Loader / streaming checkpoints (prod)';

-- COMMAND ----------

SHOW CATALOGS LIKE 'ecom_*';