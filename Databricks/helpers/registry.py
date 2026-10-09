from pyspark.sql import SparkSession
from pyspark.sql import functions as F

def ensure_classifier_registry_table(spark: SparkSession, table_name: str = "workspace.med.classifier_registry") -> None:
    # make registry table for classifier if it doesn't exist
    spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
      classifier_run_id STRING,
      created_at TIMESTAMP
    )
    USING DELTA
    """)

def append_classifier_run_id(spark: SparkSession, run_id: str, table_name: str = "workspace.med.classifier_registry") -> None:
    ensure_classifier_registry_table(spark, table_name=table_name) # ensure classifier table exists

    # add new classifier run id to table
    (
        spark.createDataFrame([(run_id,)], ["classifier_run_id"])
        .withColumn("created_at", F.current_timestamp())
        .write.format("delta")
        .mode("append")
        .saveAsTable(table_name)
    )