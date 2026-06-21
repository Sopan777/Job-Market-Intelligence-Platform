"""
Role clustering: sentence-transformers embeddings → UMAP dimensionality reduction → HDBSCAN clustering.
Embeddings are cached to disk so re-runs skip the expensive encoding step.
"""
import hashlib
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd
from tqdm import tqdm

from src.logger import get_logger

logger = get_logger(__name__)


def embed_descriptions(
    df: pd.DataFrame,
    cache_path: str = "data/processed/embeddings.npy",
    model_name: str = "all-MiniLM-L6-v2",
) -> np.ndarray:
    from sentence_transformers import SentenceTransformer

    cache = Path(cache_path)

    # Cheap fingerprint: row count + column names + first/last 100 descriptions
    # Avoids hashing all descriptions on every run while still detecting data changes
    descs = df["description"].fillna("").tolist()
    sample = descs[:100] + descs[-100:]
    fingerprint = f"{len(df)}|{list(df.columns)}|{''.join(sample)}"
    content_hash = hashlib.md5(fingerprint.encode()).hexdigest()
    hash_path = cache.with_suffix(".hash")

    if cache.exists() and hash_path.exists() and hash_path.read_text() == content_hash:
        logger.info("Loading cached embeddings from %s", cache)
        return np.load(cache)

    all_texts = df["description"].fillna("").tolist()

    # Filter empty descriptions; track original indices for reconstruction
    non_empty_idx = [i for i, t in enumerate(all_texts) if t.strip()]
    texts_to_encode = [all_texts[i] for i in non_empty_idx]
    skipped = len(all_texts) - len(texts_to_encode)

    logger.info(
        "Encoding %d non-empty descriptions (skipped %d empty) with %s...",
        len(texts_to_encode), skipped, model_name,
    )
    model = SentenceTransformer(model_name)
    partial = model.encode(texts_to_encode, batch_size=64, show_progress_bar=True, normalize_embeddings=True)

    # Reconstruct full embedding array (zero vector for empty rows)
    embed_dim = partial.shape[1]
    embeddings = np.zeros((len(all_texts), embed_dim), dtype=partial.dtype)
    for new_i, orig_i in enumerate(non_empty_idx):
        embeddings[orig_i] = partial[new_i]

    cache.parent.mkdir(parents=True, exist_ok=True)
    np.save(cache, embeddings)
    hash_path.write_text(content_hash)
    logger.info("Cached embeddings to %s", cache)
    return embeddings


def reduce_dimensions(
    embeddings: np.ndarray,
    n_components: int = 50,
    n_components_2d: int = 2,
) -> tuple[np.ndarray, np.ndarray]:
    import umap

    logger.info("UMAP: reducing %dd → %dd for clustering...", embeddings.shape[1], n_components)
    reducer_hd = umap.UMAP(
        n_components=n_components,
        n_neighbors=15,
        min_dist=0.0,
        metric="cosine",
        random_state=42,
        low_memory=len(embeddings) > 5000,
    )
    reduced_hd = reducer_hd.fit_transform(embeddings)

    logger.info("UMAP: reducing → 2d for visualization...")
    reducer_2d = umap.UMAP(
        n_components=n_components_2d,
        n_neighbors=15,
        min_dist=0.1,
        metric="cosine",
        random_state=42,
        low_memory=len(embeddings) > 5000,
    )
    reduced_2d = reducer_2d.fit_transform(embeddings)

    return reduced_hd, reduced_2d


def cluster_roles(reduced_hd: np.ndarray) -> np.ndarray:
    import hdbscan

    logger.info("HDBSCAN clustering...")
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=max(15, len(reduced_hd) // 50),  # increased from max(5, n//100)
        min_samples=3,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    labels = clusterer.fit_predict(reduced_hd)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    noise_pct = (labels == -1).mean() * 100
    logger.info("Found %d clusters, %.1f%% noise points", n_clusters, noise_pct)
    return labels


def label_clusters(df: pd.DataFrame) -> dict[int, str]:
    """Derive a human-readable name for each cluster from the most common title tokens."""
    labels = {}
    for cluster_id in sorted(df["cluster"].unique()):
        if cluster_id == -1:
            labels[-1] = "Uncategorized"
            continue
        titles = df[df["cluster"] == cluster_id]["title"].str.lower().tolist()
        tokens = []
        for t in titles:
            tokens.extend(t.split())
        stop = {"engineer", "senior", "junior", "lead", "staff", "principal", "and", "of", "the", "a"}
        token_counts = Counter(t for t in tokens if t not in stop and len(t) > 2)
        top = [w for w, _ in token_counts.most_common(3)]
        labels[cluster_id] = " / ".join(top).title() if top else f"Cluster {cluster_id}"
    return labels


def run_clustering(
    df: pd.DataFrame,
    output_path: str = "data/processed/jobs_clustered.parquet",
) -> pd.DataFrame:
    embeddings = embed_descriptions(df)
    reduced_hd, reduced_2d = reduce_dimensions(embeddings)
    cluster_labels = cluster_roles(reduced_hd)

    df = df.copy()
    df["cluster"] = cluster_labels
    df["umap_x"] = reduced_2d[:, 0]
    df["umap_y"] = reduced_2d[:, 1]

    cluster_names = label_clusters(df)
    df["cluster_name"] = df["cluster"].map(cluster_names).fillna("Uncategorized")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    logger.info("Saved %d clustered jobs to %s", len(df), out)
    return df
