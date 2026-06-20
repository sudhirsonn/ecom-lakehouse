from pyspark import pipelines as dp
from pyspark.sql.functions import col, trim, lower, to_timestamp, to_date, coalesce

catalog = spark.conf.get("catalog")

@dp.table(
    name="slv_orders",
    comment="Cleansed, deduplicated orders with standardized dates and status"
)
# Drop rows with no order key — unusable.
@dp.expect_or_drop("valid_order_id", "order_id IS NOT NULL")
# Every order must reference a customer — drop orphans (protects downstream joins).
@dp.expect_or_drop("has_customer", "customer_id IS NOT NULL")
# Status must be one of the known lifecycle values — warn on anything unexpected.
@dp.expect("known_status",
           "order_status IN ('placed','paid','shipped','delivered','canceled','returned')")
# Order total should be non-negative when present — warn (keep) to investigate.
@dp.expect("non_negative_total", "order_total IS NULL OR order_total >= 0")
# Date must parse if present — fail loudly on unknown formats.
@dp.expect("parseable_order_date", "order_date IS NULL OR order_ts IS NOT NULL")
def slv_orders():
    return (
        spark.readStream.table(f"{catalog}.`01_bronze`.br_orders")
        # dedup: one row per order_id
        .dropDuplicates(["order_id"])
        # standardize status: trim + lowercase (code-like, used for grouping)
        .withColumn("order_status", lower(trim(col("order_status"))))
        # parse the messy order_date into a real timestamp
        .withColumn("order_ts", coalesce(
            to_timestamp("order_date", "yyyy-MM-dd HH:mm:ss"),
            to_timestamp("order_date", "yyyy-MM-dd'T'HH:mm:ss"),
            to_timestamp("order_date", "MM/dd/yyyy HH:mm:ss"), 
            to_timestamp("order_date", "MM/dd/yyyy"),
            to_timestamp("order_date", "MM-dd-yyyy"),
            to_timestamp("order_date", "MM-dd-yyyy HH:mm:ss"),
            to_timestamp("order_date", "M/d/yyyy"),             
            to_timestamp("order_date", "yyyy/MM/dd"),
            to_timestamp("order_date", "dd-MM-yyyy HH:mm"),
            to_timestamp("order_date", "dd-MM-yyyy"),
            to_timestamp("order_date", "yyyy-MM-dd") 
        ))
        .select(
            "order_id",
            "customer_id",
            "order_status",
            "order_date",   # raw kept for traceability
            "order_ts",     # parsed timestamp
            "order_total"
        )
    )