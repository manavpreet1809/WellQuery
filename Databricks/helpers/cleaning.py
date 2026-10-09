from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window

def clean_and_sentence_split(raw_df: DataFrame, min_len: int = 50, sentence_split_pattern: str = r"(?<=[\.\!\?])\s+") -> DataFrame:
    raw = F.col("raw_text").cast("string") # raw text as string

    # unescape common HTML entities
    txt = F.regexp_replace(raw, "&lt;", "<")
    txt = F.regexp_replace(txt, "&gt;", ">")
    txt = F.regexp_replace(txt, "&amp;", "&")
    txt = F.regexp_replace(txt, "&quot;", "\"")

    # normalize text
    txt = F.lower(txt)
    txt = F.regexp_replace(txt, "<[^>]+>", " ") # remove HTML tags
    txt = F.regexp_replace(txt, r"[\r\n\t]+", " ") # remove line breaks/tabs
    txt = F.regexp_replace(txt, r"[^\p{L}\p{N}\p{P}\s]", " ") # remove weird characters
    txt = F.regexp_replace(txt, r"\s+", " ") # collapse whitespace
    txt = F.trim(txt)

    df = raw_df.withColumn("text_clean", txt) # add clean text
    df = df.filter(F.col("text_clean").isNotNull() & (F.length("text_clean") >= F.lit(min_len))) # filter short or empty docs
    df = df.withColumn("sentences", F.split(F.col("text_clean"), sentence_split_pattern)) # split into sentences

    # dedupe
    w = Window.partitionBy("source", "doc_id").orderBy(F.col("ingested_at").desc())
    df = (
        df.withColumn("rn", F.row_number().over(w))
          .filter(F.col("rn") == 1)
          .drop("rn")
    )

    # select final columns for docs_clean
    return df.select(
        "doc_id",
        "source",
        "category",
        "title",
        "synonyms",
        "url",
        "text_clean",
        F.col("ingested_at").alias("snapshot_ts"),
        "sentences",
    )
