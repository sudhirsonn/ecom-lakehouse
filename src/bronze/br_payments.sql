-- =============================================================
-- br_payments.sql  —  Bronze ingestion: Payments (nested installments)
--
-- PIPELINE FORM (deployed via bundle). The volume path and table
-- name use ${catalog} so each environment (dev/test/prod) creates
-- the table in its own catalog and reads its own landing zone.
-- Schema qualified to 01_bronze (pipeline default schema is 02_silver).
-- =============================================================

CREATE OR REFRESH STREAMING TABLE `01_bronze`.br_payments
COMMENT 'Payments (nested installments) — raw, ingested from landing via Auto Loader'
AS SELECT
  *,
  _metadata.file_name              AS _source_file,
  _metadata.file_modification_time AS _source_file_ts,
  current_timestamp()              AS _ingested_at
FROM STREAM read_files(
  '${landing_volume_path}/payments/',
  format              => 'json',
  schemaEvolutionMode => 'addNewColumns'
);
