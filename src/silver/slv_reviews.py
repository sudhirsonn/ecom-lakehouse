from pyspark import pipelines as dp
from pyspark.sql.functions import col, trim, to_timestamp, to_date, coalesce

catalog = spark.conf.get("catalog")

@dp.table(
    name="slv_reviews",
    comment="Flattened reviews with unpacked meta struct and parsed dates"
)

# Every review needs its own id and an order reference.
@dp.expect_or_drop("valid_review_id", "review_id IS NOT NULL")
@dp.expect_or_drop("valid_order_ref", "order_id IS NOT NULL")

# Score must be in the 1-5 range — drop anything outside it as corrupt.
@dp.expect_or_drop("valid_score", "score BETWEEN 1 AND 5")

# Date must parse if present — fail loudly on unknown formats.
@dp.expect("parseable_review_date", "review_date IS NULL OR review_ts IS NOT NULL")

def slv_reviews():
    return(
        spark.readStream.table(f"{catalog}.`01_bronze`.br_reviews")
        .withColumn("comment", trim(col("comment")))
        .withColumn("review_ts", coalesce(
            to_timestamp("review_date", "yyyy-MM-dd HH:mm:ss"),
            to_timestamp("review_date", "yyyy-MM-dd'T'HH:mm:ss"), 
            to_timestamp("review_date", "MM/dd/yyyy"),
            to_timestamp("review_date", "MM/dd/yyyy HH:mm:ss"), 
            to_timestamp("review_date", "MM-dd-yyyy"),
            to_timestamp("review_date", "MM-dd-yyyy HH:mm:ss"),
            to_timestamp("review_date", "M/d/yyyy"),                
            to_timestamp("review_date", "yyyy/MM/dd"),
            to_timestamp("review_date", "dd-MM-yyyy HH:mm"),
            to_timestamp("review_date", "dd-MM-yyyy"),
            to_timestamp("review_date", "yyyy-MM-dd") 
        ))
        .select(
            "review_id",
            "order_id",
            "score",
            "comment",
            "review_date",   # raw kept for traceability
            "review_ts",     # parsed timestamp
            col("meta.verified").alias("verified"),
            col("meta.helpful_votes").alias("helpful_votes")
        )
    )