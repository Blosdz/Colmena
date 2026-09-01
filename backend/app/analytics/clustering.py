"""K-means (harness §21, Fase 9). Función pura vía numpy (algoritmo de Lloyd).

Sin scikit-learn: k-means clásico es simple de implementar correctamente y
evita añadir esa dependencia sólo para esto.
"""

from __future__ import annotations

import numpy as np


def compute_kmeans(
    points: list[list[float]], k: int, max_iter: int = 100, seed: int = 42
) -> dict:
    data = np.asarray(points, dtype=float)
    n = data.shape[0]
    rng = np.random.default_rng(seed)
    initial_indices = rng.choice(n, size=k, replace=False)
    centroids = data[initial_indices].copy()

    labels = np.zeros(n, dtype=int)
    for iteration in range(max_iter):
        distances = np.linalg.norm(data[:, None, :] - centroids[None, :, :], axis=2)
        new_labels = np.argmin(distances, axis=1)

        if iteration > 0 and np.array_equal(new_labels, labels):
            break
        labels = new_labels

        new_centroids = np.array(
            [
                data[labels == cluster].mean(axis=0) if np.any(labels == cluster) else centroids[cluster]
                for cluster in range(k)
            ]
        )
        if np.allclose(new_centroids, centroids):
            centroids = new_centroids
            break
        centroids = new_centroids

    distances = np.linalg.norm(data - centroids[labels], axis=1)
    inertia = float(np.sum(distances**2))
    sizes = [int(np.sum(labels == cluster)) for cluster in range(k)]

    return {
        "k": k,
        "n": n,
        "labels": [int(label) for label in labels],
        "centroids": [[float(v) for v in centroid] for centroid in centroids],
        "cluster_sizes": sizes,
        "inertia": inertia,
    }
