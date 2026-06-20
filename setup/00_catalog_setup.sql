-- =============================================================
-- 00_catalog_setup.sql
-- One-time manual provisioning of the Unity Catalog hierarchy for
-- the e-commerce lakehouse. Run once by an admin in the SQL Editor.
--
-- NOT processed by the bundle — catalogs are account-level resources
-- created manually as a prerequisite. The bundle deploys the pipeline
-- and job into these pre-existing catalogs.
--
-- Pattern: catalog-per-environment isolation (dev / test / prod), each
-- backed by its own external location under the shared ADLS account.
-- Storage credential `ecom_mi` wraps the access connector's managed
-- identity and authorizes UC to access the storage account.
-- =============================================================

-- -------------------------------------------------------------
-- DEV
-- -------------------------------------------------------------
-- Landing zone (raw files) + managed location (table data) for dev.
CREATE EXTERNAL LOCATION IF NOT EXISTS ecom_landing_dev
  URL 'abfss://landing@ecomlakehousedev.dfs.core.windows.net/'
  WITH (STORAGE CREDENTIAL ecom_mi)
  COMMENT 'Raw file landing zone (shared across environments)';

CREATE EXTERNAL LOCATION IF NOT EXISTS ecom_managed_dev
  URL 'abfss://metastore-root@ecomlakehousedev.dfs.core.windows.net/dev/'
  WITH (STORAGE CREDENTIAL ecom_mi)
  COMMENT 'Managed-table storage for the dev catalog';

CREATE CATALOG IF NOT EXISTS ecom_dev
  MANAGED LOCATION 'abfss://metastore-root@ecomlakehousedev.dfs.core.windows.net/dev/'
  COMMENT 'E-commerce lakehouse — dev environment';

USE CATALOG ecom_dev;
CREATE SCHEMA IF NOT EXISTS `01_bronze` COMMENT 'Raw ingested data (Auto Loader)';
CREATE SCHEMA IF NOT EXISTS `02_silver` COMMENT 'Cleansed, conformed, validated data';
CREATE SCHEMA IF NOT EXISTS `03_gold`   COMMENT 'Star schema + materialized views for BI';

-- Volumes in dev bronze: external landing + managed checkpoints.
CREATE EXTERNAL VOLUME IF NOT EXISTS ecom_dev.`01_bronze`.raw_landing
  LOCATION 'abfss://landing@ecomlakehousedev.dfs.core.windows.net/'
  COMMENT 'External volume over the ADLS landing container';
CREATE VOLUME IF NOT EXISTS ecom_dev.`01_bronze`._checkpoints
  COMMENT 'Managed volume for Auto Loader / streaming checkpoints';

-- -------------------------------------------------------------
-- TEST
-- -------------------------------------------------------------
CREATE EXTERNAL LOCATION IF NOT EXISTS ecom_managed_test
  URL 'abfss://metastore-root@ecomlakehousedev.dfs.core.windows.net/test/'
  WITH (STORAGE CREDENTIAL ecom_mi)
  COMMENT 'Managed-table storage for the test catalog';

CREATE CATALOG IF NOT EXISTS ecom_test
  MANAGED LOCATION 'abfss://metastore-root@ecomlakehousedev.dfs.core.windows.net/test/'
  COMMENT 'E-commerce lakehouse — test environment';

USE CATALOG ecom_test;
CREATE SCHEMA IF NOT EXISTS `01_bronze` COMMENT 'Raw ingested data (Auto Loader)';
CREATE SCHEMA IF NOT EXISTS `02_silver` COMMENT 'Cleansed, conformed, validated data';
CREATE SCHEMA IF NOT EXISTS `03_gold`   COMMENT 'Star schema + materialized views for BI';

-- NOTE: the shared 'landing' container can be wrapped by only ONE external
-- volume (dev owns it). Test/prod do not declare raw_landing. If test/prod
-- needed independent ingestion, use separate landing paths (e.g. landing/test/).
CREATE VOLUME IF NOT EXISTS ecom_test.`01_bronze`._checkpoints
  COMMENT 'Managed volume for Auto Loader / streaming checkpoints (test)';

-- -------------------------------------------------------------
-- PROD
-- -------------------------------------------------------------
CREATE EXTERNAL LOCATION IF NOT EXISTS ecom_managed_prod
  URL 'abfss://metastore-root@ecomlakehousedev.dfs.core.windows.net/prod/'
  WITH (STORAGE CREDENTIAL ecom_mi)
  COMMENT 'Managed-table storage for the prod catalog';

CREATE CATALOG IF NOT EXISTS ecom_prod
  MANAGED LOCATION 'abfss://metastore-root@ecomlakehousedev.dfs.core.windows.net/prod/'
  COMMENT 'E-commerce lakehouse — prod environment';

USE CATALOG ecom_prod;
CREATE SCHEMA IF NOT EXISTS `01_bronze` COMMENT 'Raw ingested data (Auto Loader)';
CREATE SCHEMA IF NOT EXISTS `02_silver` COMMENT 'Cleansed, conformed, validated data';
CREATE SCHEMA IF NOT EXISTS `03_gold`   COMMENT 'Star schema + materialized views for BI';

-- (shared-landing constraint as noted above — prod has no raw_landing volume)
CREATE VOLUME IF NOT EXISTS ecom_prod.`01_bronze`._checkpoints
  COMMENT 'Managed volume for Auto Loader / streaming checkpoints (prod)';

-- Note: all three environments share ONE landing container; in a
-- multi-workspace prod setup you'd typically use separate storage
-- accounts per environment. Single-account here keeps the trial simple.
