from pyspark import pipelines as dp
from pyspark.sql.functions import col, explode

catalog = spark.conf.get("catalog")

@dp.table(
    name="slv_payments",
    comment="Flattened payments — one row per installment"
)

# Every payment must reference an order — drop orphans.
@dp.expect_or_drop("valid_order_ref", "order_id IS NOT NULL")

# Installment amount should be non-negative.
@dp.expect("non_negative_amount", "amount IS NULL OR amount >= 0")

# Payment type should be one of the known types — warn on anything else.
@dp.expect("known_payment_type",
           "payment_type IN ('credit_card','debit_card','voucher','boleto')")

def slv_payments():
    return(
        spark.readStream.table(f"{catalog}.`01_bronze`.br_payments")
        # explode the installments array: one row per installment
        .withColumn("installment", explode(col("installments")))
        # pull the struct fields out into flat columns
        .select(
            "order_id",
            "payment_type",
            col("installment.installment_no").alias("installment_no"),
            col("installment.amount").alias("amount"),
            col("installment.paid").alias("paid")
        )
    )