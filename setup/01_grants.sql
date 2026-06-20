-- =============================================================
-- 01_grants.sql  —  *** PHASE 7 DRAFT — NOT YET IMPLEMENTED ***
-- RBAC grants (+ ABAC column masks / row filters to be added).
-- Uses ${env} as a placeholder; will be rewritten during Governance
-- for all three catalogs (ecom_dev/test/prod) with real group names.
-- NOT processed by the bundle; run manually per environment.
-- =============================================================

-- =============================================================
-- 01_grants.sql
-- Unity Catalog permission model for the ${env} environment.
--
-- PRINCIPLE: grant to GROUPS, never individual users. Groups are
-- synced from your identity provider (Entra ID). When someone
-- joins/leaves a team, IdP membership changes and access follows
-- automatically — no SQL edits, no orphaned grants.
--
-- PRINCIPLE: least privilege per layer. Engineers build all layers;
-- analysts only read Gold; the BI service principal only reads Gold.
-- =============================================================

USE CATALOG ecom_${env};

-- Everyone who uses the catalog needs USE CATALOG (traversal only —
-- it does NOT grant read on any data).
GRANT USE CATALOG ON CATALOG ecom_${env} TO `ecom_engineers`;
GRANT USE CATALOG ON CATALOG ecom_${env} TO `ecom_analysts`;
GRANT USE CATALOG ON CATALOG ecom_${env} TO `ecom_bi_sp`;

-- Engineers: full control of Bronze and Silver (they build them).
GRANT ALL PRIVILEGES ON SCHEMA 01_bronze TO `ecom_engineers`;
GRANT ALL PRIVILEGES ON SCHEMA 02_silver TO `ecom_engineers`;
GRANT ALL PRIVILEGES ON SCHEMA 03_gold   TO `ecom_engineers`;

-- Analysts and BI: SELECT on Gold only. They never see raw or
-- intermediate data — that's both a security and a correctness
-- guarantee (no one reports off un-validated Silver by accident).
GRANT USE SCHEMA ON SCHEMA 03_gold TO `ecom_analysts`;
GRANT USE SCHEMA ON SCHEMA 03_gold TO `ecom_bi_sp`;
GRANT SELECT    ON SCHEMA 03_gold TO `ecom_analysts`;
GRANT SELECT    ON SCHEMA 03_gold TO `ecom_bi_sp`;

-- Read access to the landing volume for engineers (to inspect raw
-- files) and the pipeline service principal (to ingest them).
GRANT READ VOLUME ON VOLUME 01_bronze.raw_landing TO `ecom_engineers`;
