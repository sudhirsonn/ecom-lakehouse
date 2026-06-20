# E-Commerce Lakehouse — Project Log

A running record of decisions, setup steps, and the reasoning behind them.
Kept as both build documentation and interview-prep material.

> How to use this log: append as you go. For each step, note what you did,
> any values you generated (account names, IDs), and anything that went wrong
> + how you fixed it. The "why" notes are the parts interviewers probe.

---

## Project summary

**What:** Production-grade medallion lakehouse on Azure Databricks.
**Domain:** E-commerce (Olist-style: orders, items, payments, reviews, customers, products, sellers).
**Stack:** Azure + ADLS Gen2 + Azure Databricks + Unity Catalog + Declarative Automation Bundles + GitHub Actions CI/CD.
**Architecture:** Volumes -> Bronze -> Silver -> Gold -> BI.

**Why e-commerce:** natural streaming sources (orders, clickstream) that justify
Auto Loader and streaming tables; rich dimensional modeling with real SCD needs
(customers change address, products change price); genuine CDC use case (order
status transitions); and a domain interviewers understand instantly so the
conversation stays on architecture, not the business.

---

## Environment facts (fill in / keep current)

| Item | Value |
|---|---|
| Subscription | Azure for Students ($100 credit, no card) |
| **Working region** | **East US** (Central US was BLOCKED by student region policy) |
| Resource group | rg-ecom-lakehouse |
| Storage account | ecomlakehousedev |
| Containers | metastore-root, landing |
| Access Connector | ecom-access-connector |
| Access Connector Resource ID | __________ (paste from JSON View) |
| Databricks workspace | __________ (not created yet) |
| Date workspace created (trial clock) | __________ |

---

## Key decisions log

| Decision | Choice | Why |
|---|---|---|
| Cloud | Azure (Azure for Students) | First-party Databricks integration = easier setup; student sub gives $100 credit, no card |
| Compute | Serverless | Per-second billing, no idle cost, auto-managed sizing — best fit for spiky pipeline workloads |
| UC isolation | One catalog per environment | Hard isolation (dev job cannot read prod), clean lineage, one-line catalog swap per bundle target |
| Bundle tool | Declarative Automation Bundles | Current name for Databricks Asset Bundles; one codebase deploys to dev/test/prod via per-target variables |
| Storage auth | Access Connector + managed identity | No keys/secrets to rotate; works through storage firewalls; the secure enterprise pattern |
| Phase 1 priority | Bundle + UC setup first | Everything downstream needs a real deploy target and real objects to govern — no throwaway work |
| Support plan | None (free) | Paid plans are for production SLAs; billing/subscription help is free regardless |

---

## Cost protection (DONE)

Three nested layers. Alerts *tell* you; deletion *stops* you.

1. **Budget alerts** — Cost Management -> Budgets. $20/month budget,
   email alerts at 25% / 50% / 80% / 100%. (25% = $5 tripwire.)
2. **Low tripwire** — the 25%/$5 alert is the "something is running" signal.
   Project should idle near $0 between sessions.
3. **Kill switch** — delete resource group `rg-ecom-lakehouse`. Tears down
   every resource at once; billing stops. Redeploy from bundle in minutes.

**Cost habits:** Trial (Premium – 14-Day Free DBUs) tier for free compute;
serverless everywhere (auto-stops); small dataset (~few hundred MB);
delete resource group when stepping away > 1 day.

My budget: $20/month, alerts to sudhirsonn@hotmail.com.

---

## Naming conventions

| Object | Convention | Example |
|---|---|---|
| Catalog | ecom_{env} | ecom_prod |
| Schema | {nn}_{layer} | 02_silver |
| Bronze table | br_{source}_{entity} | br_orders |
| Silver table | slv_{entity} | slv_orders |
| Gold dimension | dim_{entity} | dim_customer |
| Gold fact | fct_{process} | fct_sales |
| Materialized view | mv_{subject}_{grain} | mv_revenue_daily |
| Volume | {purpose} | raw_landing, _checkpoints |
| Surrogate key | {entity}_sk | customer_sk |
| Business key | {entity}_id | customer_id |

Rationale worth remembering: surrogate keys (_sk) are join keys only, never
exposed to BI as meaningful; checkpoint volumes prefixed _ to flag them as
system objects.

---

## Unity Catalog hierarchy

```
Metastore (one per region)
├── ecom_dev   (bound to dev workspace)
│   ├── 01_bronze   -> volumes: raw_landing (external), _checkpoints (managed)
│   ├── 02_silver
│   └── 03_gold
├── ecom_test  (bound to test workspace)
└── ecom_prod  (bound to prod workspace)
```

External vs managed volume (common interview Q):
- raw_landing  = EXTERNAL — points at real ADLS path so upstream systems drop files there.
- _checkpoints = MANAGED  — UC owns the storage; only Spark touches it.

Managed vs external TABLE (also a common interview Q):
- Managed table  — UC owns the data, stored under metastore-root; drop = data deleted.
- External table — data lives where you specify; drop = data stays.
Storage override hierarchy: metastore -> catalog -> schema.

Two containers and why:
- landing        = raw files arrive here (you upload; Auto Loader reads via external volume).
- metastore-root = where UC physically stores managed-table bytes (UC manages; you don't touch).

---

## Setup progress tracker

### Step 0 — Architecture & design  [DONE]
Designed business case, architecture, UC hierarchy, naming, repo structure, roadmap.

### Step 1 — Azure account  [DONE]
- [x] Azure for Students subscription active
- [x] Support plan: None (free)
- [x] Cost protection: budget + 25/50/80/100% alerts
- [x] Resource group rg-ecom-lakehouse created
- Note: Free-credit pay-as-you-go signup gave "not eligible"; turned out an
  Azure for Students subscription was available, which is better ($100, no card).
- Note: Central US BLOCKED by student "allowed locations" policy
  (RequestDisallowedByAzure). East US is allowed -> East US is the project region.

### Step 2 — ADLS Gen2 storage  [DONE]
- [x] Storage account ecomlakehousedev created (East US)
- [x] Hierarchical namespace ENABLED  <- critical, makes it Gen2
- [x] Standard performance, LRS redundancy (cheapest)
- [x] Containers: metastore-root, landing

### Step 3 — Access Connector  [IN PROGRESS]
- [x] ecom-access-connector created (East US)
- [x] System-assigned managed identity ON
- [ ] Granted "Storage Blob Data Contributor" on ecomlakehousedev  <- DO THIS
- [ ] Resource ID copied (paste above): __________
- Why managed identity not keys: no secrets to rotate, works through firewalls.
- Role must be Storage Blob Data Contributor (not plain Contributor, not Reader).

### Step 4 — Databricks workspace  [TODO] (starts 14-day trial clock)
- [ ] Workspace created (name: ecom-databricks, region: East US)
- [ ] Pricing tier: Trial (Premium – 14-Day Free DBUs)

### Step 5 — Unity Catalog metastore  [TODO]
- [ ] Metastore created in account console (East US)
- [ ] Points at metastore-root ADLS path + Access Connector resource ID
- [ ] Workspace assigned to metastore
- Note: metastore is an ACCOUNT-level object (one per region), not workspace-level.

### Step 6 — Bundle + UC provisioning  [TODO]
- [ ] CLI installed + authenticated (databricks auth login)
- [ ] databricks.yml host URLs + storage_account values filled in
- [ ] Setup SQL run (00_catalog_setup.sql, 01_grants.sql)
- [ ] databricks bundle validate -t dev passes

---

## Phase roadmap

| Phase | Build | Status |
|---|---|---|
| 0 | Architecture & design | DONE |
| 1 | Azure foundation + UC provisioning | DONE |
| 2 | Bronze: Auto Loader + streaming tables (SQL) | DONE |
| 3 | Silver: PySpark transforms + DQ expectations | DONE |
| 4 | Gold: SCD2 dims, facts, MERGE, materialized views | DONE |
| 5 | Orchestration: Lakeflow Job DAG | DONE |
| 6 | CI/CD: GitHub Actions, dev->test->prod | TODO |
| 7 | Governance: RBAC + ABAC + lineage | TODO |
| 8 | BI: Tableau dashboards (exec/customer/product/ops) | TODO |
| 9 | End-to-end testing & validation pass | TODO |

### Governance commitment (Phase 7 detail)
Full access-control spectrum — deliberately covering all three layers:
- **Expectations** (data quality) — implemented in Silver (Phase 3) via
  CONSTRAINT ... EXPECT (...) ON VIOLATION. Validates cleansed output.
- **RBAC** (coarse access) — group-based grants, least privilege per layer.
  Engineers: all layers. Analysts + BI SP: SELECT on Gold only.
- **ABAC** (fine-grained access) — at least one column mask (e.g. mask
  customer email / PII) and one row filter (e.g. region-scoped order access),
  plus tag-based policies. This is the differentiator vs basic-grants projects.
- **Lineage** — UC tracks table + column lineage automatically; surface it.

Interview angle: covering expectations + RBAC + ABAC demonstrates the full
governance spectrum, which senior DE roles specifically probe.

---

## Gotchas hit (real-world experience for interviews)

- **Student region policy:** Azure for Students enforces an "allowed locations"
  Azure Policy. Central US was denied (RequestDisallowedByAzure). Checked
  Policy -> Assignments to find allowed regions; used East US. Lesson: student/
  restricted subs can't deploy everywhere; check the policy, don't guess.
- **Resource group region vs resource region:** RG metadata stayed Central US
  but resources go in East US — that's fine, RG region is just metadata. Cleaner
  to match, but resources inside a group can live in a different region.

---

---

## Phase 2 — Bronze (DONE)

7 streaming tables in ecom_dev.`01_bronze`, ingested via Auto Loader (SQL read_files):
- br_orders (~5100 rows, 5000 distinct — dupes kept on purpose)
- br_customers (~2060)  br_products (800)  br_sellers (300)
- br_order_items (~12761)
- br_payments (~5100, JSON, nested installments array)
- br_reviews (~1128, JSON, nested meta struct)

Repo files: src/bronze/br_*.sql — one CREATE per file, interactive form now,
pipeline form (drop catalog qualifier) in Phase 5.

Key facts learned / gotchas:
- read_files() is Auto Loader's SQL interface; cloudFiles is the PySpark one;
  cloud_files() is deprecated. Databricks Assistant suggested wrong variants.
- Streaming tables (SQL) require a SQL Warehouse, NOT generic serverless compute
  (error: ST_NOT_ENABLED_ON_SERVERLESS_GENERIC_COMPUTE). Ran from SQL Editor.
- Triggered mode: runs, processes new files, stops. Not always-on. Cost-efficient.
- schemaEvolutionMode => 'addNewColumns'. Directory-listing mode (default), fine
  at this volume; file-notification (Event Grid + queue) only pays off at millions.
- SQL streaming tables manage checkpoint/schema state automatically (no
  schemaLocation/checkpointLocation needed — that's the PySpark cloudFiles path).
- Pipeline source files = declarative definitions only (one table/file), no
  verification SELECTs.
- Schema kept numeric-prefixed (01_bronze) => backtick-quote everywhere.

---

---

## Phase 3 — Silver (DONE)

7 tables in ecom_dev.`02_silver`, built as Lakeflow Declarative Pipeline
(pyspark.pipelines / dp), serverless, in pipeline `ecom_silver`:
- slv_customers (~2000, dedup + city/state standardize + date parse)
- slv_products (795, dropped 5 negative prices; 41 null weights flagged)
- slv_sellers (~300, state standardize)
- slv_orders (5000, dedup 5100->5000, status+date+total checks)
- slv_order_items (12515, composite-key dedup, 3 FK guards, 250 null prices flagged)
- slv_payments (JSON: explode installments array -> one row per installment)
- slv_reviews (~2155, JSON: dot-notation on meta struct, no explode)

Key patterns / interview points:
- DROP vs ALLOW per rule: DROP = corrupt data that poisons downstream
  (neg price, bad score, orphan FK, bad qty). ALLOW/warn = flag-but-keep
  (missing email/weight/price).
- Dedup on actual grain: single key for dims, composite (order_id+item_seq)
  for line items.
- Conform shared fields identically across tables (state uppercased same way).
- Messy dates: coalesce known formats + a parse-failure expectation that
  fails loudly; keep raw value for traceability.
- Nested JSON: explode for ARRAYS (changes grain), dot-notation for STRUCTS
  (same grain). Array vs struct drives technique.
- FK guards with DROP protect referential integrity before the fact layer.
- dp code runs only inside a pipeline; one table per file in transformations/.
- Run file (single new table) vs Run pipeline (whole DAG).

---

---

## Phase 4 — Gold (DONE)

Star schema in ecom_dev.`03_gold` (same pipeline, SQL + Python mix):

Dimensions:
- dim_date (MV) — generated calendar, date_sk = yyyyMMdd int
- dim_product (MV, SCD1) — xxhash64 SK + Unknown member (sk=-1) for orphans
- dim_seller (MV, SCD1)
- dim_customer (streaming table, SCD2 via create_auto_cdc_flow; __START_AT/__END_AT)
- dim_customer_keyed (MV) — adds customer_sk = xxhash64(customer_id, __START_AT),
  friendly valid_from/valid_to/is_current

Fact:
- fct_sales (MV) — grain: order line item; measures qty, unit_price, revenue;
  FKs to all 4 dims; INNER join orders, LEFT join dims; COALESCE(product_sk,-1).
  Revenue + unit_price guarded: CASE WHEN unit_price > 0 (invalid -> null).

Materialized views (dashboard feeds):
- mv_revenue_daily (Exec) — shows seasonal trend
- mv_sales_by_category (Product) — shows category skew + unknown bucket
- mv_sales_by_state (Customer) — geographic concentration
- mv_order_funnel (Operational) — status funnel, driven from slv_orders
- mv_review_summary (Operational) — score distribution (4-5 heavy), window fn for pct

Key lessons / interview points:
- Surrogate keys: decouple from business keys; ESSENTIAL for SCD2 (per-version key);
  hash not sequential for distributed-friendliness; applied to all dims for consistency.
- SCD2 declarative (create_auto_cdc_flow) manages validity but NOT surrogate key ->
  keyed presentation view adds it (hash of business key + __START_AT).
- create_auto_cdc_flow uses imperative API (no @dp.table decorator).
- Referential integrity: DQ drops in Silver orphaned 93 facts -> Kimball Unknown
  member (sk=-1) + COALESCE so orphans visible, not silent/lost. Detected via
  key-resolution count check (has_prod < total).
- Propagating DQ: orphans carried negative prices into revenue -> fact-level
  validity guard (CASE WHEN unit_price>0) so invalid -> null everywhere. Fix once
  at the fact (DRY), not per view.
- Grain matters: COUNT(DISTINCT order_id) for orders (fact is line-item grain);
  funnel drives from slv_orders to keep orders with no line items.
- Gold mixes SQL (facts, MVs, SCD1 dims) + Python (SCD2 flow) in one pipeline.

---

---

## Phase 5 — Orchestration (DONE)

Multi-task Lakeflow Job `ecom_medallion_job` (Job ID 171872826308554):
- Task 1: bronze_refresh (SQL task) -> runs bronze_refresh.sql (7 REFRESH
  STREAMING TABLE statements), Serverless Starter Warehouse. ~5 min.
- Task 2: silver_gold_pipeline (Pipeline task) -> runs ecom_medallion_pipeline,
  Depends on bronze_refresh, Run if = All succeeded. ~1.5 min.
- Schedule: daily (job-level trigger).
- Notifications: email on failure (job-level).
- Validated end-to-end manually (6m 23s, both green) BEFORE scheduling.

Design / interview points:
- Separated ingestion (Bronze) from transformation (Silver/Gold) as two tasks
  rather than one pipeline -> different cadence/ownership; standard pattern;
  demonstrates dependency wiring. Avoided the table-ownership conflict of
  consolidating interactively-created Bronze into the pipeline.
- "Run if All succeeded" => transformations never run on failed ingestion.
- Prove-it-works-manually-then-schedule discipline.
- Two-layer model: pipeline = transformation DAG, job = operational scheduler.
- Plain REFRESH (incremental) not FULL in the scheduled refresh.

---

---

## Phase 9 — End-to-End Testing & Validation (PLANNED, do at the end)

Run AFTER Governance (so masks/filters are tested too), before/with BI.
A deliberate validation pass that produces demonstrable portfolio evidence.

Test suite:
1. NEW-DATA FLOW (incremental ingestion): drop a new file into a landing
   folder, run the job, confirm Bronze ingests only new rows (not reprocessing),
   Silver/Gold update, counts increase by the expected amount. Proves the
   scheduled incremental-ingestion story.
2. SCD TYPE 2 HISTORY (the headline demo): change an existing customer's city,
   re-ingest, confirm dim_customer creates a 2nd version row (old expired:
   valid_to set + is_current=false; new current). Show a point-in-time query.
   We have NOT yet seen SCD2 produce multiple versions (no changes in data yet).
3. DQ EXPECTATIONS CATCHING BAD DATA: drop a file with a negative price, null
   key, malformed email; confirm DQ dashboard drops/flags them, metrics move.
4. FAILURE ALERTING: deliberately break a task, confirm failure email arrives,
   then fix. Proves monitoring.
5. ORPHAN HANDLING: add an order_item referencing a non-existent product,
   confirm it lands in the 'unknown' bucket (sk=-1), not lost/broken.
6. CI/CD DEPLOY (after Phase 6): deploy via bundle to a fresh target, prove the
   stack stands up from code.
7. GOVERNANCE ENFORCEMENT (after Phase 7): query as restricted role, confirm
   column masks hide PII and row filters limit rows.

## Portfolio polish artifacts (TODO, alongside testing)
- README + architecture diagram (landing->Bronze->Silver->Gold->BI + job). TOP priority.
- UC lineage graph screenshot (Bronze->Silver->Gold->dashboards).
- DQ expectations dashboard screenshot with real catch metrics.
- Cost notes (serverless, ~6 min/day per run).
- Cleaned-up PROJECT_LOG as evidence of decision-making.
- SCD2 two-version screenshot, failure-email screenshot.

---

---

## Phase 6 — CI/CD (IN PROGRESS)

Decisions:
- Source control + CI/CD: GitHub + GitHub Actions (account created). Public repo
  doubles as portfolio showcase. GitHub Actions free for public repos.
- Bundles: "Declarative Automation Bundles" (formerly Databricks Asset Bundles),
  the recommended CI/CD approach. CLI: databricks bundle validate/deploy/run.
- Environment promotion: OPTION A - single workspace, multi-catalog targets.
  dev -> ecom_dev, test -> ecom_test, prod -> ecom_prod (catalog-per-env isolation,
  matches our original UC architecture decision). Bundle targets swap catalog +
  resource naming. Avoids multi-workspace overhead; demonstrates full pattern.
  Interview note: "multi-workspace for physical isolation in a larger org; used
  catalog-level isolation in one workspace to show the pattern within scope."

Prereqs checklist:
- [x] GitHub account
- [ ] Databricks CLI installed locally
- [ ] Git installed locally
- [ ] Service principal + token for GitHub auth (create together)
- [ ] Workspace host URL
- [ ] Create ecom_test + ecom_prod catalogs (have ecom_dev)

To build: finalize databricks.yml (dev/test/prod targets), resources/*.yml for the
job + pipeline, .github/workflows (validate on PR, deploy on merge), auth via SP token.

---

### Phase 6 update — per-environment landing (Option B / hybrid -> full isolation)
Chose isolated per-env landing paths. UC LOCATION_OVERLAP forced moving dev off
the container root: dev's raw_landing now wraps landing/dev/ (was root), so all
three envs are siblings: landing/dev/, landing/test/, landing/prod/.
- dev: full dataset (~5k orders) re-staged under landing/dev/, volume repointed,
  Bronze FULL-refreshed. Bronze code unchanged (volume name raw_landing stable).
- test: ~500-order sample under landing/test/, own raw_landing + _checkpoints.
- prod: ~1500-order sample under landing/prod/, own raw_landing + _checkpoints.
- Samples generated with different seeds (genuinely different data, not copies).
- Interview point: true environment isolation - separate catalog AND separate
  landing path per env; landing path becomes a bundle variable. UC enforces
  one-volume-per-path (no parent/child overlap), which drove the sibling layout.
- KEY: landing path must now be parameterized in the bundle (like catalog), since
  Bronze reads differ per env (/dev/, /test/, /prod/).

---

### Phase 6 update — Bronze brought INTO the pipeline (Option 1)
Reversed the earlier "Bronze separate" decision for CI/CD reproducibility.
- All 7 Bronze SQL files parameterized: ${catalog} in both table name and the
  read_files volume path -> each env creates Bronze in its own catalog reading
  its own landing zone. Schema qualified to `01_bronze` (pipeline default is 02_silver).
- pipeline.yml globs now include ../src/bronze/** (pipeline builds Bronze->Silver->Gold).
- job.yml SIMPLIFIED: single pipeline task (no more separate bronze_refresh SQL task;
  the pipeline now creates+refreshes Bronze). warehouse_id no longer needed by the job.
- Silver/Gold files still hardcode ecom_dev -> must be parameterized to ${catalog}
  when exported into the bundle (next step).
- RECONCILIATION needed in dev: existing interactively-created Bronze tables
  (standalone streaming tables) conflict with pipeline-managed ones. Must drop the
  interactive br_* in dev and let the pipeline take ownership on first run.
- Interview point: migrated Bronze from hand-built prototype to code-defined,
  pipeline-managed, parameterized-per-env — the IaC/CI-CD-correct approach.

---

## Glossary of "why" answers (interview prep)

- **Why serverless?** Per-second billing + no idle cost + no spin-up wait. Wins for
  spiky pipeline workloads vs a warm classic cluster. Classic only wins for sustained 24/7.
- **Why catalog-per-env not schema-per-env?** Hard physical isolation + clean
  permission grants. dev_bronze/prod_bronze schemas in one catalog fail the isolation test.
- **Why managed identity not storage keys?** No secrets in code, nothing to rotate,
  works through storage firewalls. The Access Connector holds the identity; you grant
  it Storage Blob Data Contributor; Unity Catalog uses it. Keys are a master password — avoid.
- **Why grant to groups not users?** Groups sync from the identity provider; access
  follows team membership automatically — no SQL edits, no orphaned grants.
- **Why bundle variables per target?** One codebase, three environments, zero
  duplication. Same SQL provisions dev/test/prod by swapping ${env} + ${storage_account}.
- **Why Bronze=SQL, Silver=PySpark, Gold=both?** Bronze ingestion is declarative
  (SQL fits); Silver needs procedural cleansing/dedup logic (PySpark fits); Gold
  mixes set-based facts (SQL) with reusable dimension MERGE logic (PySpark).
