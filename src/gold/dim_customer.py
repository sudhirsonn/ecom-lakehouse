from pyspark import pipelines as dp
from pyspark.sql.functions import col

catalog = spark.conf.get("catalog")

# 1. Declare the target streaming table that will hold the SCD2 dimension
dp.create_streaming_table(
    name=f"{catalog}.`03_gold`.dim_customer",
    comment="Customer dimension (SCD Type 2 — full history with validity windows)"
)

# 2. Define the auto-CDC flow that maintains SCD2 history
dp.create_auto_cdc_flow(
    target=f"{catalog}.`03_gold`.dim_customer",
    source=f"{catalog}.`02_silver`.slv_customers",
    keys=["customer_id"],
    sequence_by=col("signup_ts"),
    stored_as_scd_type=2
)