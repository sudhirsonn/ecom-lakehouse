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
| Access Connector Resource ID | /subscriptions/88ded80a-561a-486f-8d85-6e60302fb74b/resourceGroups/rg-ecom-lakehouse/providers/Microsoft.Databricks/accessConnectors/ecom-access-connector |
| Databricks workspace | ecom-databricks created in East US |
| Date workspace created (trial clock) | June 16, 2026 — 14-day trial clock started. Trial ends ~June 30. |

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
   email alerts at 25% / 50% / 75% / 100%. (25% = $5 tripwire.)
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

### Step 3 — Access Connector  [DONE]
- ecom-access-connector created (East US)
- System-assigned managed identity ON
- Granted "Storage Blob Data Contributor" on ecomlakehousedev
- Resource ID: /subscriptions/**********-561a-486f-8d85-6e60302fb74b/resourceGroups/rg-ecom-lakehouse/providers/Microsoft.Databricks/accessConnectors/ecom-access-connector
- Why managed identity not keys: no secrets to rotate, works through firewalls.
- Role must be Storage Blob Data Contributor (not plain Contributor, not Reader).

### Step 4 — Databricks workspace  [DONE] (14-day trial clock started)
- Workspace name: ecom-databricks, region: East US
- Pricing tier: Trial (Premium – 14-Day Free DBUs)
- Trial started June 16 2026, ends ~June 30 2026.

### Step 5 — Unity Catalog metastore  [DONE]
- Metastore created in account console (East US)
- Points at metastore-root ADLS path + Access Connector resource ID
- Workspace assigned to metastore
- Note: metastore is an ACCOUNT-level object (one per region), not workspace-level.

### Step 6 — UC provisioning  [DONE]
- Storage credential ecom_mi (wraps the Access Connector managed identity)
- External locations: ecom_landing_dev (→ landing container), ecom_managed_dev (→ metastore-root/dev/)
- Schemas: 01_bronze, 02_silver, 03_gold
- Volumes: raw_landing (external → landing), _checkpoints (managed)
- Verified with SHOW SCHEMAS / SHOW VOLUMES

### Step 7 — Bundle + CI/CD  [DONE — see Phase 6 entries]
- CLI installed + authenticated (databricks auth login)
- Bundle validated, deployed, and running across test + prod via GitHub Actions

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
| 6 | CI/CD: GitHub Actions, dev->test->prod | DONE |
| 7 | Governance: RBAC + ABAC + lineage | DONE |
| 8 | Tableau Story & BI Layer | DONE |
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

## Phase 9 — End-to-End Testing & Validation (DONE)

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
5. CI/CD DEPLOY (after Phase 6): deploy via bundle to a fresh target, prove the
   stack stands up from code.
6. GOVERNANCE ENFORCEMENT (after Phase 7): query as restricted role, confirm
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

## Phase 6 — CI/CD (COMPLETE)

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

### Phase 6 update — bundle validates
`databricks bundle validate -t dev` => "Validation OK!". Whole project is now
valid IaC. All source parameterized: Bronze/Gold SQL use ${catalog}; Silver +
dim_customer Python use catalog = spark.conf.get("catalog") + f"{catalog}...".
pipeline.yml passes catalog + bundle.target in configuration. Job simplified to
one pipeline task (Bronze now in-pipeline). Next: deploy -t dev (reconcile the
interactively-built dev Bronze tables — drop them, let pipeline own them), then
deploy -t test as the clean from-scratch proof, then GitHub repo + Actions + SP auth.

---

### Phase 6 — BUNDLE DEPLOYS AND RUNS SUCCESSFULLY IN TEST (major milestone)
`databricks bundle deploy -t test` + `run` => full Bronze->Silver->Gold pipeline
green in ecom_test, built entirely from code, zero manual clicks. dim_customer
(SCD2) 200 rows, fct_sales 1.3K rows, all 5 MVs populated, scale proportional
to the ~500-order test sample.

THREE DISTINCT PARAMETERIZATION MECHANISMS (this was the hard-won lesson):
1. BUNDLE-level (${var.catalog}) - resolved by the CLI at deploy time, ONLY
   works reliably in databricks.yml / resources/*.yml (the YAML files
   themselves), NOT inside SQL/Python source-file string literals (silently
   vanished there - manifested as "Syntax error near '.'" with empty catalog,
   then a literal double "||  ||" when tried via concatenation).
2. PIPELINE-level (${param_name} in SQL): a genuine, documented mechanism
   (Lakeflow "pipeline parameters"), set via the pipeline's `configuration:`
   block and referenced by bare ${key} in SQL STRING LITERALS only (e.g. the
   read_files path). Key must be a non-reserved, distinctive name - using
   "catalog" as the config key risked colliding with the pipeline's own
   reserved `catalog:` field; renamed to `landing_volume_path` to be safe.
3. SQL TABLE REFERENCES need NO substitution at all - unqualified table names
   (just `` `01_bronze`.br_orders `` or `` `03_gold`.fct_sales ``, no catalog
   prefix) automatically resolve to the pipeline's own `catalog:` setting.
   This was the simplest fix and applied to ALL Gold SQL files + Bronze table
   names (only the volume-path STRING in Bronze needed the parameter trick).
4. PYTHON files read pipeline config via `spark.conf.get("catalog")` (Spark
   runtime config) - a totally separate mechanism from SQL's ${} substitution.
   Broke when `catalog` was temporarily removed from the pipeline's
   `configuration:` block while fixing SQL; fixed by keeping BOTH `catalog`
   and `landing_volume_path` as separate configuration keys, each serving a
   different layer (Python conf-read vs SQL string substitution).

Final pipeline.yml configuration block:
  configuration:
    catalog: ${var.catalog}              # read by Python via spark.conf.get
    landing_volume_path: "/Volumes/${var.catalog}/01_bronze/raw_landing"  # SQL ${} substitution
    bundle.target: ${bundle.target}

Interview point: debugging this required distinguishing WHEN each ${...} token
is resolved (CLI deploy-time vs pipeline parse-time vs Spark runtime) and BY
WHAT (bundle YAML processor vs Lakeflow SQL parameter engine vs spark.conf) -
three different systems sharing similar-looking syntax. Isolated one file at a
time, read each error literally (empty substitution vs reserved-word collision
vs missing config), fixed each layer with the mechanism actually meant for it
rather than forcing one syntax everywhere.

NEXT: apply same fixes to dev (reconcile interactive Bronze tables -> let
pipeline own them), deploy -t prod, then GitHub repo + Actions + SP auth.

---

### Dev scheduled-job incident: DELTA_SOURCE_IGNORE_DELETE (RESOLVED)
First scheduled run (6am) of ecom_medallion_job in DEV failed on slv_sellers and
other Silver tables: [DELTA_SOURCE_IGNORE_DELETE] "detected deleted data" from
the streaming source.

ROOT CAUSE: Structured Streaming assumes APPEND-ONLY sources. The earlier FULL
refresh of Bronze (required after migrating landing paths to per-env isolation
- dev raw_landing repointed root -> /dev/) rewrote Bronze's underlying Delta
files. From Silver's streaming-read perspective this looked like a delete
(old files gone, replaced by new ones) -> Delta correctly refused to silently
reconcile and threw the error rather than risk wrong results.

FIRST ATTEMPT (failed): plain SQL `REFRESH STREAMING TABLE ... FULL` directly
on slv_sellers -> blocked with REFRESH_DELTA_LIVE_TABLE: tables owned by a
Lakeflow pipeline can ONLY be refreshed THROUGH the pipeline, never via
standalone SQL once they're @dp.table-managed. Pipeline is the sole valid
entry point for lifecycle ops on its tables (protects internal state:
checkpoints, expectations, lineage).

FIX: Pipeline UI -> "Run pipeline" dropdown -> Full refresh all. Resets every
managed table's streaming checkpoint, rebuilds cleanly against Bronze's
current (post-migration) state. Succeeded. Scheduled job should run cleanly
incrementally going forward (no more routine Bronze FULL refreshes expected).

Interview points:
- Streaming assumes append-only; non-append changes upstream (FULL refresh,
  file rewrites) break downstream incremental reads by design - not a bug.
- Pipeline-owned tables can't be touched by ad-hoc SQL; refresh/ops must go
  through the pipeline itself once a table is @dp.table-managed.

---

### Phase 6 — PROD DEPLOY SUCCEEDED. CI/CD core demonstration complete.
`databricks bundle deploy -t prod` + `run` => full medallion built in ecom_prod
from the identical bundle codebase (only the catalog variable differs). Same
parameterization fixes from test carried over cleanly - no new issues.

STATUS: the same bundle now deploys/runs correctly across test + prod (both
fully bundle-managed, isolated catalogs, isolated landing zones, different
data volumes). Dev remains the original interactively-built environment
(pre-CI/CD prototype) - left as-is by deliberate choice (low risk/reward to
touch a working environment; test+prod together already fully prove the
promotion story).

Remaining for Phase 6: GitHub repo + push code, service principal + token for
GitHub Actions auth, get validate.yml/deploy.yml actually running on push/PR
(currently only run manually via local CLI).

---

### Phase 6 — COMPLETE
GitHub Actions deploy.yml triggered automatically on push to main, ran
"Deploy to test" end-to-end (checkout -> setup-cli -> databricks bundle deploy
-t test) in 8s, fully green. Full CI/CD loop proven: push code -> Action
triggers -> bundle deploys automatically, zero manual CLI intervention.

Auth: used a personal access token (not a dedicated service principal) for
GitHub Actions auth, stored as SP_TOKEN repo secret + DATABRICKS_HOST repo
variable. Pragmatic choice: Account Console access was blocked by an Azure/
Entra tenant restriction on the student subscription ("account does not exist
in tenant... needs to be added as external user"). Documented tradeoff: a
dedicated service principal is the production-correct least-privilege
approach; a PAT is a legitimate, simpler choice for a solo project.

Repo: public, github.com/sudhirsonn/ecom-lakehouse.

PHASE 6 SUMMARY (full picture):
- Declarative Automation Bundle (databricks.yml + resources/) - single
  workspace, catalog-per-environment promotion (dev/test/prod).
- Bronze brought INTO the pipeline (reversed earlier "keep separate" decision)
  for true CI/CD reproducibility; job simplified to one pipeline task.
- Per-environment landing isolation: landing/dev/, landing/test/, landing/prod/
  (UC enforces one-volume-per-path, forced moving dev off the container root).
- Three parameterization mechanisms identified and correctly applied:
  bundle YAML vars, Lakeflow SQL pipeline parameters, Spark Python runtime conf.
- Validated, deployed, and RAN successfully in test (ecom_test) and prod
  (ecom_prod) from one codebase. Dev left as the original interactive
  prototype by deliberate choice.
- Hit and resolved: LOCATION_OVERLAP, table-ownership conflicts, 3 distinct
  ${} substitution failures, DELTA_SOURCE_IGNORE_DELETE post-FULL-refresh,
  REFRESH_DELTA_LIVE_TABLE (pipeline-owned tables can't be SQL-refreshed
  directly), GitHub auth account mismatch, Account Console tenant block.
- GitHub Actions: validate-on-PR + deploy-on-push, both wired and proven live.

---

### Phase 6 — FULLY COMPLETE: manual-approval gate added for prod
Extended deploy.yml with a deploy-prod job (needs: deploy-test, environment:
production). GitHub Environment "production" configured with:
- Required reviewers: sudhirsonn (self) - "Allow administrators to bypass"
  deliberately UNCHECKED so the gate genuinely applies even to the admin/owner.
- Deployment branch rule: only `main` may deploy to this environment.

Verified live: push to main -> deploy-test ran automatically (16s, green) ->
deploy-prod paused in "Waiting" state with a Review pending deployments dialog
-> manually clicked Approve and deploy -> deploy-prod ran and succeeded (10s,
green). Full continuous-to-test / gated-to-prod pattern proven end-to-end with
screenshots at every stage (push -> auto test deploy -> pending prod approval
-> approved -> prod deployed).

PHASE 6 IS NOW GENUINELY COMPLETE: bundle + parameterization + per-env
isolation + GitHub repo + Actions (validate-on-PR, deploy-on-push) + gated
prod approval. Nothing partial remaining.

Interview point: "Test deploys continuously on every push for fast feedback;
production requires a human approval gate scoped to a GitHub Environment,
restricted to the main branch, with no admin bypass - so the protection is
real, not just a checkbox. This demonstrates the standard 'continuous
delivery to staging, controlled promotion to production' pattern."

---

### Phase 6 — refined: deployment vs. execution deliberately decoupled
Considered adding `databricks bundle run` after deploy in BOTH test and prod.
Caught and corrected before committing: auto-running a full PROD data pipeline
as a side-effect of every code push conflates two different concerns (code
deployment vs. data processing cadence) and risks an unrelated commit
accidentally triggering a real prod run.

FINAL DESIGN:
- deploy-test: deploy AND run once (smoke-test) - legitimate "did this
  deployment actually work" fast-feedback check, appropriate for a
  low-stakes environment.
- deploy-prod: deploy ONLY. Execution stays owned by the job's own schedule
  (currently paused, unpause when wanted) or an explicit manual/CLI trigger
  - never an automatic consequence of a code push.

Interview point: "I deliberately decoupled deployment from execution in
production - GitHub Actions ensures the prod pipeline definition is correctly
updated, but doesn't trigger a production data run as a side effect, since
deploying code and processing production data are different concerns that
shouldn't be automatically coupled. Test gets a smoke-test run for fast
feedback since the stakes are low; prod's execution stays on its own
schedule/explicit trigger."

---

### Phase 6 — FINAL: full branch-based promotion flow proven end-to-end
Reconsidered and corrected an over-engineered "deploy-dev" idea: realized
hands-on development happens directly in the ecom_dev catalog (the workbench,
unrelated to Git) and does NOT need a Git branch/PR for every iteration -
only a finished, discrete change gets branched and PR'd for promotion. This
meant the earlier dev-reconciliation/deletion plan was unnecessary and was
correctly abandoned - no dev tables or pipelines were touched.

FINAL, PROVEN ARCHITECTURE:
  feature/<branch>  --push-->        [nothing deploys]
                     --PR opened-->   validate.yml runs (bundle validate -t dev,
                                       structure check only, no deploy)
                     --merge to main--> deploy.yml triggers:
                                          deploy-test (auto: deploy + smoke-test
                                            run) succeeds
                                          deploy-prod (gated: production
                                            GitHub Environment, required
                                            reviewer, main-only, no admin
                                            bypass) -> approved -> succeeds

Verified live end-to-end with screenshots at every stage: branch push (no
deploy) -> PR opens -> validate succeeds (6s, "Validate (dev target)") ->
PR shows "All checks passed" / "not deployed" -> merge -> deploy-test auto
green (11s) -> deploy-prod "waiting for review" -> approved -> deploy-prod
green (11s) -> run summary shows "sudhirsonn approved now -> production".

This is now a complete, realistic, professional CI/CD pattern: branch
protection + automated PR validation + staged auto-deploy to test + gated
human-approved promotion to prod. PHASE 6 IS DEFINITIVELY COMPLETE.

---

### Phase 6 — SCOPE LOCKED (final)
Explored Databricks Repos as a way to eliminate manual copy-paste between
workspace edits and bundle source files. Decided NOT to adopt it - adds a
second editing surface and pipeline-parameter complexity for marginal benefit
over the existing workflow. Noted as a known, optional future enhancement,
not a gap.

CONFIRMED FINAL SCOPE for Phase 6 (nothing further needed):
- Bundle deploys to test + prod from one parameterized codebase. DONE.
- validate.yml on every PR, deploy.yml (test auto, prod gated) on merge. DONE.
- Feature branch -> PR -> merge -> approve cycle, proven live. DONE.
- Dev stays the interactive sandbox, edited directly in the Databricks UI,
  outside Git/CI-CD entirely - by deliberate design, not omission.
- Promoting a dev change to test/prod = manually port the (re-parameterized)
  change into the local bundle file, then run the normal branch/PR cycle.
  This manual step is an accepted, documented trade-off, not a defect.

PHASE 6 IS COMPLETE. No further CI/CD work required before moving on.

---

---

## Phase 7 — Governance (COMPLETE)

### RBAC
Wrote real (non-templated) 01_grants.sql for ecom_dev: 3 groups created via
Workspace -> Settings -> Identity and access -> Groups (account-console-free
route, avoided the earlier Entra tenant block):
- ecom_engineers: ALL PRIVILEGES across 01_bronze/02_silver/03_gold.
- ecom_analysts: USE CATALOG/SCHEMA + SELECT on 03_gold ONLY (Bronze/Silver
  invisible to them - no USE SCHEMA grant there at all).
- ecom_bi_reader: same base as analysts; row filter narrows further (next).
USE CATALOG/USE SCHEMA = traversal only, grants no data access by themselves;
SELECT is what actually allows reading rows.

### ABAC - column mask (email)
mask_email(email) function: is_account_group_member('ecom_engineers') ->
real value, else redacted. is_account_group_member() checks live, per-query,
against the CALLER's group membership - dynamic, not baked in at creation.

KEY LESSON - masks need different ALTER syntax per object type:
  TABLE                -> ALTER TABLE ... ALTER COLUMN ... SET MASK ...
  MATERIALIZED VIEW     -> ALTER MATERIALIZED VIEW ... ALTER COLUMN ... SET MASK ...
  VIEW                  -> ALTER VIEW ... (where supported)
ALTER TABLE failed on dim_customer_keyed (it's a materialized view, not a
table) -> applied successfully on the base table dim_customer (a real
streaming table) -> ALTER VIEW failed on dim_customer_keyed -> ALTER
MATERIALIZED VIEW succeeded. Mask now independently enforced at BOTH layers
(base table + presentation view), each evaluating the same group check.

Tested by temporarily removing self from ecom_engineers (still a member of
ecom_analysts) -> email correctly redacted -> re-added to ecom_engineers.

Interview point: "Unity Catalog masks require object-type-specific ALTER
syntax - tables, materialized views, and views each have their own ALTER
... SET MASK form. I confirmed this empirically when ALTER TABLE failed on
a materialized view and ALTER MATERIALIZED VIEW was the actual fix."

NEXT: row filter (ecom_bi_reader, region-scoped), then lineage surface,
then close out Phase 7.

---

### ABAC - row filter (geography)
filter_by_region(state) function: RETURNS BOOLEAN (required contract for row
filters - UC calls it once per row, true=visible/false=hidden; contrast with
masks which RETURN the transformed value, e.g. STRING). engineers/analysts
always pass; ecom_bi_reader only passes when state = 'TX'.

Applied with ALTER MATERIALIZED VIEW ... SET ROW FILTER ... ON (state) on
mv_sales_by_state (same object-type lesson as the column mask - materialized
views need the MATERIALIZED VIEW keyword, not TABLE or VIEW).

Tested: limited to ecom_bi_reader only -> query returned ONLY the TX row.
Restored ecom_engineers membership afterward.

PHASE 7 CORE (RBAC + ABAC) COMPLETE:
- RBAC: 3 groups, layered grants (engineers=all, analysts=Gold read-only,
  bi_reader=Gold read-only).
- ABAC column mask: email redacted unless ecom_engineers, enforced on both
  the base table and the presentation materialized view.
- ABAC row filter: bi_reader geographically restricted to TX, enforced on
  mv_sales_by_state.
- Both controls use is_account_group_member() for dynamic, per-query,
  per-caller enforcement - not static/baked-in at creation time.

Interview point: "I implemented the full access-control spectrum on top of
RBAC grants: a column mask redacting PII based on group membership, and a
row filter restricting geographic scope - both using is_account_group_member()
for live, per-query enforcement, and both required the ALTER MATERIALIZED
VIEW syntax once applied above the base streaming table, which I confirmed
by testing actual group-membership changes against the live data."

NEXT: lineage (already automatic via UC - just verify/screenshot), then
Phase 7 done.

---

### ABAC - tag-based CREATE POLICY (attempted, blocked at account-tier)
Attempted Databricks' newer declarative ABAC: CREATE POLICY ... COLUMN MASK
... TO `account users` ... MATCH COLUMNS has_tag_value('sensitivity','pii')
ON COLUMN pii_col - the auto-discovery mechanism (tag a column once, policy
applies to ANY column carrying that tag, vs. our earlier function attached
per-table by name).

Got through function creation and CREATE POLICY syntax cleanly. Final error:
[UC_INVALID_POLICY_CONDITION] Unknown tag policy key `sensitivity`.

ROOT CAUSE: CREATE POLICY requires GOVERNED tags, not the plain ALTER TABLE
... SET TAGS (...) we used (which creates an UNGOVERNED/free-text tag).
Governed tags must be registered at the ACCOUNT level first - same Account
Console area blocked earlier by the Entra tenant restriction
("account does not exist in tenant... needs to be added as external user")
when setting up the GitHub Actions service principal.

DECISION: documented as understood-but-platform-blocked, not pursued further
given time constraints. The function-based mask + row filter (both tested
live) already demonstrate the full ABAC capability; CREATE POLICY is the
more scalable NEXT step (tag once, govern many columns automatically)
correctly understood and correctly attempted, blocked only by account-tier
access on the student subscription - not a knowledge gap.

Interview point: "I implemented and live-tested function-based column masks
and row filters. I also attempted Databricks' tag-based CREATE POLICY
mechanism - which auto-applies governance to any column carrying a tag,
rather than wiring logic per-table - and correctly diagnosed why it failed:
it requires governed tags registered at the account level, which was blocked
by the same Azure/Entra tenant restriction I hit setting up CI/CD auth. I
can explain the governed-tag model and the syntax even though full
provisioning wasn't available in this environment."

PHASE 7 IS COMPLETE.

---

### UPDATE: tag-based CREATE POLICY actually succeeded
Reversal of the prior "blocked at account tier" entry. Governed Tags admin
screen (Catalog Explorer -> Governed Tags) WAS accessible, unlike the broader
Account Console that blocked SP creation - different admin surfaces, different
access. Registered governed tag key `sensitivity` with allowed value `pii`,
re-applied ALTER COLUMN ... SET TAGS using the now-governed key, re-ran
CREATE POLICY pii_email_policy -> succeeded.

PHASE 7 ABAC IS NOW FULLY COMPLETE INCLUDING THE TAG-BASED POLICY:
- Function-based column mask + row filter (manual, per-table wiring) - tested live.
- Tag-based CREATE POLICY (auto-applies to ANY column tagged sensitivity=pii,
  across any table, with zero per-table wiring) - the more scalable,
  enterprise-grade mechanism - WORKING, not just understood/attempted.

Interview point: "I implemented governance at two levels of sophistication:
manually-wired column masks and row filters for explicit per-table control,
and a tag-based ABAC policy using governed tags and CREATE POLICY, where
tagging any column sensitivity=pii automatically applies masking without
touching that table's grants individually - the pattern that scales to a
data estate with hundreds of tables rather than one bespoke rule per column."

---

### Note: governed-tag/policy propagation delay observed
After re-adding self to ecom_engineers, the column still showed masked for a
short window before resolving correctly - consistent with documented
behavior that tag/permission changes can take a few minutes to propagate.
No fix needed; resolved on its own. Worth knowing operationally: don't assume
a mask/policy is broken immediately after a group-membership change - allow
a short propagation window before debugging further.

---

### Phase 8 — BI Layer (COMPLETE)

Tool: Tableau Desktop (14-day trial, no credit card required).
Connected live to Azure Databricks through the official Databricks connector using:
- Databricks SQL Warehouse
- ODBC Driver
- Personal Access Token (PAT)

A live connection was intentionally chosen to demonstrate a production-style
architecture where dashboards query governed Gold-layer data directly rather than
relying on static extracts.

Confirmed Tableau Public cannot live-connect to Databricks (Public only accepts
file uploads). OData via CData API Server is a workaround but requires paid
third-party product. Tableau Desktop trial is the correct, free, working path.

## BI Architecture

```
ADLS Gen2
    │
Auto Loader
    │
Bronze
    │
Silver
    │
Gold Star Schema
    │
Materialized Views
    │
Databricks SQL Warehouse
    │
Tableau Desktop (Live Connection)
    │
Tableau Story
```

## Tableau Story Design

Implemented as a Tableau Story consisting of five connected story points:
1. E-Commerce Performance Overview
2. 56% of Revenue Comes from Electronics
3. 51% of Revenue Comes from California and Texas
4. 75% of Customer Reviews Are Positive
5. 70% of Orders Are Successfully Delivered

Design standards:
- Consistent purple color palette
- Large executive KPI cards
- Value labels on all bars
- Reference lines where appropriate
- Business insight panel on every page
- Live connection to Gold-layer materialized views

### Story Point 1 — E-Commerce Performance Overview
Source: mv_revenue_daily
KPIs:
- Total Revenue: $1,154,185
- Total Orders: 1,500
Visuals:
- Revenue by Month (average reference line $96K)
- Daily Revenue Trend (average reference line $89K)
Finding:
- Revenue peaked in April at approximately $160K.

### Story Point 2 — Revenue Concentration by Category
Source: mv_sales_by_category
Headline: 56% of Revenue Comes from Electronics
Visuals:
- Pareto Analysis (Revenue + Cumulative %)
- Units Sold by Category
Findings:
- Electronics generated $648K revenue.
- Electronics represents 56% of total revenue.
- Top 3 categories contribute approximately 80% of revenue.

### Story Point 3 — Geographic Revenue Concentration
Source: mv_sales_by_state
Headline: 51% of Revenue Comes from California and Texas
KPI: Top 2 States Revenue Share: 51.1%
Findings:
- CA: $300K
- TX: $290K
- NY: $196K
- FL: $145K
- IL: $140K

### Story Point 4 — Customer Satisfaction Analysis
Source: mv_review_summary
Headline: 75% of Customer Reviews Are Positive
KPIs:
- Positive Reviews: 74.6%
- Average Rating: 4.6 / 5
Review distribution:
- 5★: 290
- 4★: 189
- 3★: 76
- 2★: 58
- 1★: 29

### Story Point 5 — Operational Performance
Source: mv_order_funnel
Headline: 70% of Orders Are Successfully Delivered
KPIs:
- Delivery Rate: 70.0%
- Cancellation Rate: 3.9%
- Return Rate: 1.5%
- Operational Health: GOOD
Supporting Metrics:
- Delivered: 1,050
- Cancelled: 58
- Returned: 22
- Total Orders: 1,500

### Phase 8 Summary
Completed a production-style BI layer built on governed Gold materialized views.
The Tableau Story demonstrates:
- Executive KPI reporting
- Pareto analysis
- Geographic analysis
- Customer satisfaction analytics
- Operational performance monitoring
Phase 8 is COMPLETE.

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

---

## Verbatim interview talking points (from build log — use these in interviews)

### Bronze layer

"Bronze ingests seven raw entities via Auto Loader — five CSV sources and two JSON. I used SQL read_files with the STREAM keyword, which is Auto Loader's SQL interface, because Bronze ingestion is declarative."

"The layer preserves raw fidelity — no cleansing. I add only ingestion metadata: source filename, file modification time, and load timestamp, which makes the data auditable and reprocessable."

"Each table is a streaming table backed by a serverless Lakeflow pipeline, running in triggered mode — it processes new files and stops, which is cost-efficient. Auto Loader's checkpoint state makes every refresh incremental and idempotent."

"Schema evolution is enabled (addNewColumns) so new columns in future files expand the table rather than breaking ingestion. I used directory-listing mode since the source is low-volume; file notification only pays off at millions of files."

"The JSON sources land with their nested structure intact — payments carry a nested installments array, reviews a nested meta struct — which Silver flattens. Demonstrating both flat and nested ingestion was deliberate."

"Streaming tables created via SQL must run on a SQL Warehouse, not generic compute, because of the Lakeflow pipeline backing — a constraint I hit and resolved."

"I kept the duplicates and messy data untouched in Bronze by design — cleansing belongs in Silver. My Bronze orders shows 5,100 rows but 5,000 distinct IDs, and that gap is intentional, to be resolved downstream."

"Pipelines run in triggered mode (run-process-stop) rather than continuous, since batch analytics doesn't need always-on compute. During development I use development mode for warm compute and fast iteration; the bundle sets production mode for deployed environments."

### Silver layer

"Silver turns raw Bronze into clean, conformed, trustworthy data using Lakeflow Declarative Pipelines — PySpark transforms inside @dp.table, with data quality expectations as first-class governance."

"My expectation actions encode business judgment: DROP for unambiguously corrupt data that would poison downstream (negative prices, invalid scores, orphan records, bad quantities), ALLOW/warn for issues worth flagging but not fatal (missing emails, missing weights, missing prices). The DROP-vs-ALLOW choice per rule reflects whether the anomaly is corruption or just a gap."

"I deduplicate on each table's actual grain — single key for dimensions, composite key (order_id + item_seq) for line items — and conform shared fields identically across tables, like uppercasing state the same way in customers and sellers so geographic joins don't split."

"For messy dates I parse known formats via coalesce and add a parse-failure expectation that fails loudly if a date is present but unparseable, keeping the raw value alongside the parsed one for traceability — so a new format surfaces as a metric, not a silent null."

"For nested JSON I matched technique to structure: explode for the payments installments array (fans out to one row per installment, changing grain), and dot-notation struct extraction for the reviews meta object (one row in, one out). Array versus struct drives the approach."

"Referential integrity is guarded with DROP expectations on foreign keys before data reaches the fact layer — orphan orders and orphan line items can't propagate into the star schema."

### Gold layer

"Gold is a Kimball star schema: a central fact (fct_sales at line-item grain) surrounded by conformed dimensions, joined on surrogate keys. SCD2 on dim_customer for history, SCD1 on product/seller, plus a generated date dimension."

"Surrogate keys decouple facts from volatile business keys and are essential for SCD2 — one customer has multiple version rows sharing a business key, so the fact references a per-version surrogate key to know which version was current at event time. I used deterministic hashes rather than sequential integers for distributed-friendliness."

"I implemented SCD2 with Lakeflow's declarative auto-CDC flow, then layered a keyed presentation view to add the surrogate key and friendly valid_from/valid_to/is_current columns, since the declarative flow manages validity but not the surrogate key."

"I caught a real referential-integrity issue with a key-resolution check: data quality filtering dropped invalid products in Silver, orphaning 93 facts. I applied the Kimball Unknown-member pattern — a sentinel dimension row that orphans map to via COALESCE — so no sales are lost and the issue surfaces as a visible 'unknown' category rather than a silent null."

"That issue propagated: the orphaned facts carried negative prices into revenue. I added a fact-level validity guard so invalid prices produce null, not negative — fixing it once at the fact so every downstream view inherits clean values, rather than patching each view."

"Materialized views pre-aggregate the fact for fast dashboard reads. A recurring subtlety: because the fact is at line-item grain, order counts use COUNT(DISTINCT order_id) to avoid overcounting, and the funnel view drives from the orders table (not the fact) to count every order including those with no line items."

### Orchestration

"I orchestrated the medallion with a Lakeflow Job: a single pipeline task runs the full Bronze→Silver→Gold DAG. After initially separating Bronze (SQL task) from Silver/Gold (pipeline task), I brought Bronze into the pipeline for genuine CI/CD reproducibility — a hand-built table can't be promoted via a bundle deploy."

"I validated the job end-to-end manually before attaching a schedule — proving it works on-demand first, then automating. The full run was ~6 minutes."

"The job runs on a daily schedule with failure notifications, so new files landing in storage get picked up automatically and I'm alerted if anything breaks."

### CI/CD

"I deployed the same medallion pipeline across isolated dev/test/prod catalogs via a Declarative Automation Bundle. The trickiest part was that Databricks has three separate ${...} parameterization mechanisms — bundle-level variables resolved at deploy time, Lakeflow pipeline parameters resolved at parse time, and Spark runtime config read in Python — that look identical but are processed by completely different systems. I debugged it by isolating one file at a time and reading each failure precisely."

"Structured Streaming assumes append-only sources. When I did a FULL refresh on Bronze (necessary after migrating the landing paths to per-environment isolation), it rewrote the underlying files, which looked like a delete to the downstream Silver stream — Delta correctly refused to silently reconcile non-append changes and threw DELTA_SOURCE_IGNORE_DELETE. The fix was a one-time full refresh of Silver via the pipeline UI."

"Once a table is owned by a declarative pipeline, you can't refresh it with standalone SQL — the pipeline is the sole entry point for its lifecycle, which is enforced specifically so ad-hoc operations can't corrupt the pipeline's internal state (checkpoints, expectations, lineage)."

### General architecture

"Raw files land in the ADLS landing container the way an upstream system would write them; Databricks ingests via an external volume over that container using Auto Loader — so the storage layer and the compute layer are cleanly separated."

"Used Auto Loader in directory-listing mode (the default) since the source volume is small and low-velocity; file-notification mode with Event Grid + storage queue would only pay off at millions of files, where directory listing becomes expensive."

"Volumes are governance boundaries over directories, not per-file or per-folder objects; you split them by access policy, not by data organization."

"Streaming tables and materialized views created via SQL must run on a SQL Warehouse, not generic/all-purpose compute, because they're backed by serverless Lakeflow Declarative Pipelines."

"Pipeline source files contain only declarative table definitions — one per file. Verification and exploration queries are kept separate so the pipeline files stay clean and the dependency graph is unambiguous."
