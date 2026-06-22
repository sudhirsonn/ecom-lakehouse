from pyspark import pipelines as dp
from pyspark.sql.functions import col, trim, initcap, upper, to_timestamp, to_date, coalesce

catalog = spark.conf.get("catalog")

@dp.table(
    name="slv_customers",
    comment="Cleansed, deduplicated, standardized customer data"
)

# Drop rows with no business key — those are unusable.
@dp.expect_or_drop("valid_customer_id", "customer_id IS NOT NULL")

# Warn (keep) on bad email format — we still want the customer record.
@dp.expect("valid_email_format","email is NULL OR email RLIKE '^[^@]+@[^@]+\.[^@]+$'")

@dp.expect("parseable_signup_date","signup_date IS NULL or signup_ts IS NOT NULL")

def slv_customers():
    return (
        spark.readStream.table(f"{catalog}.`01_bronze`.br_customers")
        # standardize city: trim whitespace + title-case
        .withColumn("city", initcap(trim(col("city"))))
        # standardize state: trim + uppercase
        .withColumn("state", upper(trim(col("state"))))
        # normalize email: trim (null stays null)
        .withColumn("email", trim(col("email")))
        # Parse the messy signup_date. Try known formats in order; first match wins.
        # NOTE: ambiguous formats (MM/dd vs dd/MM) are resolved by ORDER here
        .withColumn("signup_ts", coalesce(
            to_timestamp("signup_date", "yyyy-MM-dd HH:mm:ss"),
            to_timestamp("signup_date", "yyyy-MM-dd'T'HH:mm:ss"),   # ISO 8601
            to_timestamp("signup_date", "MM/dd/yyyy"),
            to_timestamp("signup_date", "MM/dd/yyyy HH:mm:ss"), 
            to_timestamp("signup_date", "MM-dd-yyyy"),
            to_timestamp("signup_date", "MM-dd-yyyy HH:mm:ss"),
            to_timestamp("signup_date", "M/d/yyyy"),                # single-digit US
            to_timestamp("signup_date", "yyyy/MM/dd"),
            to_timestamp("signup_date", "dd-MM-yyyy HH:mm"),
            to_timestamp("signup_date", "dd-MM-yyyy"),
            to_timestamp("signup_date", "yyyy-MM-dd") 
        ))
        # dedup: one row per customer_id        
        .dropDuplicates(["customer_id", "signup_ts"])
        .select("customer_id", "customer_name", "email", "city", "state", "signup_date", "signup_ts")
    )