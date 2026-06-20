from pyspark import pipelines as dp
from pyspark.sql.functions import col

catalog = spark.conf.get("catalog")

@dp.table(
    name="slv_order_items",
    comment="Cleansed order line items with referential and value checks"
)

# Drop rows missing the composite key parts — unusable.
@dp.expect_or_drop("valid_order_ref", "order_id IS NOT NULL")
@dp.expect_or_drop("valid_item_seq", "item_seq IS NOT NULL")

# Line item must reference a product and seller — drop orphans (protects joins).
@dp.expect_or_drop("has_product", "product_id IS NOT NULL")
@dp.expect_or_drop("has_seller", "seller_id IS NOT NULL")

# Quantity must be positive — a line with <= 0 qty is invalid.
@dp.expect_or_drop("positive_quantity", "quantity > 0")

# Unit price may be missing (warn, keep) — we can still count the line.
@dp.expect("unit_price_present", "unit_price IS NOT NULL")

def slv_order_items():
    return(
        spark.readStream.table(f"{catalog}.`01_bronze`.br_order_items")
        # dedup on the composite key (a line is unique per order + sequence)
        .dropDuplicates(["order_id", "item_seq"])
        .select(
            "order_id",
            "item_seq",
            "product_id",
            "seller_id",
            "quantity",
            "unit_price"
        )
        
    )