from pyspark import pipelines as dp
from pyspark.sql.functions import col, trim, lower, initcap

catalog = spark.conf.get("catalog")

@dp.table(
    name="slv_products",
    comment="Cleansed, standardized products"
)

# Drop rows with no product key
@dp.expect_or_drop("valid_product_id", "product_id IS NOT NULL")
# Drop rows with invalid (negative or zero) price — a product can't cost <= 0.
@dp.expect_or_drop("positive_price", "base_price > 0")
# Warn when weight is missing — still a usable product record.
@dp.expect("weight_present", "weight_grams IS NOT NULL")

def slv_products():
    return (
        spark.readStream.table(f"{catalog}.`01_bronze`.br_products")
        .dropDuplicates(["product_id"])
        .withColumn("product_category", lower(trim(col("product_category"))))
        .withColumn("product_name", trim(col("product_name")))
        .select(
            "product_id",
            "product_category",
            "product_name",
            "base_price",
            "weight_grams"
        )
    )    