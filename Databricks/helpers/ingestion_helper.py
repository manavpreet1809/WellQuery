from typing import List
from pyspark.sql import DataFrame, Row, SparkSession
from pyspark.sql.functions import lit, current_timestamp, col, split, trim, expr, regexp_replace
from pyspark.sql.types import ArrayType, StringType, StructType, StructField

CATALOG = "workspace"
SCHEMA = "med"
RAW_TABLE = f"{CATALOG}.{SCHEMA}.raw_data"

RAW_RECORD_SCHEMA = StructType([
    StructField("doc_id", StringType(), False),
    StructField("category", StringType(), True),
    StructField("title", StringType(), True),
    StructField("synonyms", StringType(), True),
    StructField("url", StringType(), True),
    StructField("raw_text", StringType(), True),
    StructField("meta_json", StringType(), True),
])

# ensure table exists, if not create it
def ensure_raw_table(spark: SparkSession):
    create_ddl = f"""
    CREATE TABLE IF NOT EXISTS {RAW_TABLE} (
        doc_id STRING,
        category STRING,
        source STRING,
        title STRING,
        synonyms ARRAY<STRING>,
        url STRING,
        raw_text STRING,
        meta_json STRING,
        ingested_at TIMESTAMP
    )
    USING DELTA
    """
    spark.sql(create_ddl)

def cast_synonyms_to_array(df: DataFrame, colname: str = "synonyms") -> DataFrame:
    # if the column doesnt exist, return a empty array
    if colname not in df.columns:
        return df.withColumn(colname, lit(None).cast("array<string>"))

    dtype = dict(df.dtypes).get(colname)

    if dtype and dtype.startswith("array"):
        return df.withColumn(colname, col(colname).cast(ArrayType(StringType())))

    from pyspark.sql.functions import regexp_replace

    df = df.withColumn(colname, regexp_replace(col(colname), ";", ",")) # convert semicolon to comma
    df = df.withColumn(colname, split(col(colname), ",").cast("array<string>")) # split into array
    df = df.withColumn(colname, expr(f"transform({colname}, x -> trim(x))")) # trim each value

    return df

def standardize_docs(df: DataFrame, source_value: str) -> DataFrame:
    required: List[str] = ["doc_id", "category", "title", "synonyms", "url", "raw_text", "meta_json"] # enforce columns

    for c in required:
        if c not in df.columns:
            df = df.withColumn(c, lit(None).cast("string")) # fill missing columns

    df = cast_synonyms_to_array(df, "synonyms") # cast synonyms to array

    return (
        df.select(*required)
            .withColumn("source", lit(source_value))
            .withColumn("ingested_at", current_timestamp())
    )

def write_raw_docs(df: DataFrame):
    (df.write.format("delta").mode("append").saveAsTable(RAW_TABLE))

def overwrite_source(df: DataFrame, source_value: str):
    (
        df.write
          .format("delta")
          .mode("overwrite")
          .option("replaceWhere", f"source = '{source_value}'")
          .saveAsTable(RAW_TABLE)
    )

def load_records_to_raw_data(spark: SparkSession, records: List[dict], source_value: str) -> None:
    if not records:
        print(f"No records to load for source {source_value}")
        return

    df = spark.createDataFrame([Row(**r) for r in records], schema=RAW_RECORD_SCHEMA) # create dataframe from list of python dicts using the strict schema

    standardized = standardize_docs(df, source_value=source_value) # reshape and match the normal layout
    overwrite_source(standardized, source_value=source_value)