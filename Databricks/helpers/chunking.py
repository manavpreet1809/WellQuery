from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window

def build_doc_chunks(docs_clean_df: DataFrame, chunk_size: int = 800) -> DataFrame:
    # expand sentences into rows with sentence indexes
    expanded = (
        docs_clean_df.select(
            "doc_id",
            "source",
            "category",
            "title",
            "synonyms",
            "url",
            "snapshot_ts",
            F.posexplode("sentences").alias("sentence_index", "sentence"),
        )
        .filter(F.col("sentence").isNotNull() & (F.col("sentence") != ""))
    )

    # window to compute cumulative character length per doc in sentence order
    w = (
        Window.partitionBy("doc_id")
        .orderBy(F.col("sentence_index"))
        .rowsBetween(Window.unboundedPreceding, Window.currentRow)
    )

    # compute lengths and cumulative length
    expanded = expanded.withColumn("sentence_len", F.length("sentence"))
    expanded = expanded.withColumn("cum_len", F.sum(F.col("sentence_len") + F.lit(1)).over(w))

    # assign each sentence to a chunk group based on cumulative length
    expanded = expanded.withColumn(
        "chunk_group",
        ((F.col("cum_len") - F.lit(1)) / F.lit(chunk_size)).cast("int"),
    )

    # collect sentences per chunk group
    chunks_df = (
        expanded.groupBy(
            "doc_id",
            "source",
            "category",
            "title",
            "synonyms",
            "url",
            "snapshot_ts",
            "chunk_group",
        )
        .agg(F.collect_list("sentence").alias("sentences_in_chunk"))
    )

    # join sentences into one string per chunk
    chunks_df = chunks_df.withColumn("chunk_text", F.concat_ws(" ", F.col("sentences_in_chunk")))

    # use chunk_group as chunk_index
    chunks_df = chunks_df.withColumn("chunk_index", F.col("chunk_group"))

    # create chunk_id as doc_id_{chunk_index}
    chunks_df = chunks_df.withColumn(
        "chunk_id",
        F.concat(F.col("doc_id"), F.lit("_"), F.col("chunk_index").cast("string")),
    )

    # select final schema
    return chunks_df.select(
        "doc_id",
        "source",
        "chunk_id",
        "chunk_index",
        "chunk_text",
        "title",
        "category",
        "url",
        "synonyms",
        "snapshot_ts",
    )
