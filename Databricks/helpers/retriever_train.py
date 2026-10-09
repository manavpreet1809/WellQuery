from typing import Tuple, Dict, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.neighbors import NearestNeighbors
from scipy.sparse import csr_matrix

def build_vectorizer(word_max_features: int = 50000, char_max_features: int = 100000) -> FeatureUnion:
    word_vec = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),
        stop_words="english",
        min_df=2,
        max_df=0.8,
        sublinear_tf=True,
        max_features=word_max_features,
    )

    char_vec = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=2,
        max_df=0.9,
        sublinear_tf=True,
        max_features=char_max_features,
    )

    return FeatureUnion([("word", word_vec), ("char", char_vec)])

def train_tfidf_knn(texts: List[str], n_neighbors: int = 10) -> Tuple[FeatureUnion, NearestNeighbors, csr_matrix]:
    vectorizer = build_vectorizer()
    matrix = vectorizer.fit_transform(texts)

    knn = NearestNeighbors(
        n_neighbors=n_neighbors,
        metric="cosine",
        algorithm="brute",
        n_jobs=1,
    ).fit(matrix)

    return vectorizer, knn, matrix

def default_retriever_params(n_neighbors: int = 10) -> Dict:
    return {
        "word_ngram_range": "(1,2)",
        "word_stop_words": "english",
        "word_min_df": 2,
        "word_max_df": 0.8,
        "word_sublinear_tf": True,
        "word_max_features": 50000,
        "char_analyzer": "char_wb",
        "char_ngram_range": "(3,5)",
        "char_min_df": 2,
        "char_max_df": 0.9,
        "char_sublinear_tf": True,
        "char_max_features": 100000,
        "knn_metric": "cosine",
        "knn_algorithm": "brute",
        "knn_n_neighbors": n_neighbors,
    }
