from typing import List, Optional
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
import pandas as pd

def build_classifier_training_df(
    spark: SparkSession,
    source_table: str = "workspace.med.doc_chunks",
    allowed_labels: Optional[List[str]] = None,
    chunk_text_max_chars: int = 1200,
    min_rows_per_class: int = 200,
) -> pd.DataFrame:
    allowed_labels = allowed_labels or ["drug", "condition"]

    # load chunked data from delta table and keep only needed columns
    df = (
        spark.table(source_table)
        .select("doc_id", "chunk_id", "category", "title", "synonyms", "chunk_text")
        .where(F.col("category").isin(allowed_labels))
    )

    # join synonyms into single string, trim chunk text, link fields to form training text
    df = (
        df.withColumn("syn_join", F.concat_ws(" ", F.col("synonyms")))
        .withColumn("chunk_trim", F.expr(f"substring(chunk_text, 1, {int(chunk_text_max_chars)})"))
        .withColumn(
            "train_text",
            F.concat_ws(
                " ",
                F.coalesce(F.col("title"), F.lit("")),
                F.coalesce(F.col("syn_join"), F.lit("")),
                F.coalesce(F.col("chunk_trim"), F.lit("")),
            ),
        )
        .select("doc_id", "chunk_id", F.col("category").alias("label"), "train_text")
        .where(F.length(F.col("train_text")) > 0)
    )

    # check that we have enough rows for each class
    counts = df.groupBy("label").count().toPandas()
    counts_map = dict(zip(counts["label"], counts["count"]))

    # raise error if not enough data
    for lab in allowed_labels:
        if counts_map.get(lab, 0) < min_rows_per_class:
            raise RuntimeError(
                f"Not enough rows for label '{lab}'. Found {counts_map.get(lab, 0)}."
            )

    pdf = df.toPandas()
    return pdf