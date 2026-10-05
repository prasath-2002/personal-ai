from functools import lru_cache

import numpy as np


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Load the embedding model only when it is
    actually needed.

    First run may take some time because the
    model has to be downloaded/cached.
    """

    print(
        f"Loading local embedding model: {MODEL_NAME}"
    )

    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(
        MODEL_NAME
    )

    print(
        "Local embedding model loaded."
    )

    return model


def generate_embedding(
    text: str,
) -> list[float]:
    """
    Convert text into a semantic vector.

    No OpenAI/Groq API call is made.
    """

    clean_text = text.strip()

    if not clean_text:
        return []

    model = get_embedding_model()

    embedding = model.encode(
        clean_text,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    return embedding.tolist()


def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    """
    Because embeddings are normalized,
    dot product gives cosine similarity.
    """

    if not vector_a or not vector_b:
        return 0.0

    a = np.asarray(
        vector_a,
        dtype=np.float32,
    )

    b = np.asarray(
        vector_b,
        dtype=np.float32,
    )

    if a.shape != b.shape:
        return 0.0

    return float(
        np.dot(a, b)
    )