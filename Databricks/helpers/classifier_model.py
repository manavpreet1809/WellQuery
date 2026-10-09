from typing import Tuple
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

def build_logreg_router(
    ngram_range: Tuple[int, int] = (1, 2),
    word_max_features: int = 100000,
    min_df: int = 2,
    max_df: float = 0.9,
    logreg_c: float = 2.0,
    max_iter: int = 2000,
) -> Pipeline:
    # sklearn pipeline with TF-IDF and Logistic Regression
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    analyzer="word", # tokenize by words
                    ngram_range=ngram_range, # use unigrams and bigrams
                    stop_words="english", # remove common english stopwords
                    min_df=min_df, # ignore very rare terms
                    max_df=max_df, # ignore overly common terms
                    sublinear_tf=True, # use log scaling to term frequencies
                    max_features=word_max_features, # limit vocab size
                ),
            ),
            (
                "logreg",
                LogisticRegression(
                    solver="lbfgs", # use for multinomial classification
                    C=logreg_c, # strictness of the model
                    max_iter=max_iter, # max number of learning steps the model can take
                    n_jobs=1, # run on a single core
                    class_weight="balanced", # treat rare categories just as important as common ones
                ),
            ),
        ]
    )