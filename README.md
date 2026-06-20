# E-Commerce Lakehouse (Azure Databricks)

Production-grade medallion lakehouse on Azure Databricks + Unity Catalog,
deployed via Declarative Automation Bundles and GitHub Actions.

## Architecture
Landing (ADLS) -> Bronze (Auto Loader streaming tables, SQL)
-> Silver (PySpark declarative pipeline + data quality expectations)
-> Gold (Kimball star schema: SCD2 customer dim, SCD1 dims, fact, materialized views)
-> BI (Tableau dashboards)

Orchestrated by a multi-task Lakeflow Job (Bronze refresh -> Silver/Gold pipeline),
scheduled daily with failure alerts.

## Layers
- **Bronze** (`src/bronze/`): 7 streaming tables via Auto Loader `read_files`, raw fidelity + ingestion metadata, schema evolution.
- **Silver** (`src/silver/`): cleansing, dedup, conforming, JSON flattening, DQ expectations (DROP vs ALLOW).
- **Gold** (`src/gold/`): star schema — surrogate keys, SCD2 (`dim_customer`), Unknown-member orphan handling, fact-level validity guards, 5 materialized views.

## CI/CD
- **Bundle** (`databricks.yml`, `resources/`): single-workspace, catalog-per-environment promotion (ecom_dev/test/prod).
- **GitHub Actions** (`.github/workflows/`): validate on PR, deploy on merge.

## Environments
Catalog-per-environment isolation: `ecom_dev`, `ecom_test`, `ecom_prod`,
each with `01_bronze` / `02_silver` / `03_gold` schemas.

## Data
Synthetic Olist-style e-commerce dataset (~5k orders) with realistic skew
(category concentration, metro geography, seasonal revenue, review distribution)
and deliberate messiness for the cleansing layer to handle.
