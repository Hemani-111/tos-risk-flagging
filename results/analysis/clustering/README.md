# K-means Clustering Analysis

## What this analysis tests

Unsupervised K-means clustering on training-only MiniLM embeddings (384-d, local CPU). Tests k=3, 5, 8, 12 with three independent seeds. Reports cosine silhouette, ARI stability across seeds, cluster sizes, and descriptive label composition.

## Important clarification

K-means is an **unsupervised method**. Clusters are **NOT risk labels** and are not used for classification. Cluster composition is described only after fitting, to understand whether clusters mix risk categories.

## Canonical outputs

| Protocol | File | Description |
|----------|------|-------------|
| primary | `results/experiments/ensemble_calibration_primary_v1/kmeans_cluster_summary.csv` | Per-k cluster summary |
| primary | `results/experiments/ensemble_calibration_primary_v1/kmeans_train_assignments.csv` | Train point → cluster assignments |
| primary | `results/experiments/ensemble_calibration_primary_v1/pca_train_coordinates.csv` | 2-D PCA coordinates for visualization |
| clause | `results/experiments/ensemble_calibration_clause_v1/kmeans_cluster_summary.csv` | Per-k cluster summary |
| clause | `results/experiments/ensemble_calibration_clause_v1/kmeans_train_assignments.csv` | Train point → cluster assignments |
| clause | `results/experiments/ensemble_calibration_clause_v1/pca_train_coordinates.csv` | 2-D PCA coordinates for visualization |

## Key findings (development-only)

| Protocol | k range | Cosine silhouette | Stability (ARI) | Conclusion |
|----------|---------|-------------------|-----------------|------------|
| Primary | 3, 5, 8, 12 | ~0.075–0.098 | Falls at larger k | Exploratory only |
| Clause | 3, 5, 8, 12 | ~0.075–0.098 | Falls at larger k | Exploratory only |

Weak silhouette scores and declining stability indicate clusters do not form well-separated groups. Clusters mix risk categories and are not deployed as labels.

## Runnable entry point

```
python results/analysis/clustering/run.py --protocol both
python results/analysis/clustering/run.py --protocol primary --smoke
```
