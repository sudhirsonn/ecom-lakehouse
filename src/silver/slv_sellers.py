from pyspark import pipelines as dp
from pyspark.sql.functions import col, trim, upper, initcap

catalog = spark.conf.get("catalog")

@dp.table(
    name="slv_sellers",
    comment="Cleansed, standardized sellers"
)

# Drop rows with no seller key — unusable.
@dp.expect_or_drop("valid_seller_id", "seller_id IS NOT NULL")
# Warn if seller name is missing — keep the record but flag it.
@dp.expect("seller_name_present", "seller_name IS NOT NULL")

def slv_sellers():
    return (
        spark.readStream.table(f"{catalog}.`01_bronze`.br_sellers")
        .dropDuplicates(["seller_id"])
        # tidy city: trim + title-case (proper noun)
        .withColumn("seller_city", initcap(trim(col("seller_city"))))
        # standardize state: trim + uppercase (code-like)
        .withColumn("seller_state", upper(trim(col("seller_state"))))
        # tidy seller name: trim stray whitespace
        .withColumn("seller_name", trim(col("seller_name")))
        .select(
            "seller_id",
            "seller_name",
            "seller_city",
            "seller_state"
        )
    )