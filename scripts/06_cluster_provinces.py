"""
Script 06: Province Emotion Clustering
Hierarchical clustering + agglomerative K search.
Outputs: linkage/silhouette CSVs and cluster labels.
PNG diagnostics are optional via SAVE_MATPLOTLIB_PLOTS=1.
"""
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path
from math import sqrt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import linkage

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
ANALYSIS_DIR = ROOT / "analysis"
TMP_DIR = ROOT / "tmp"

FEATURE_COLS = [
    "joy_mean_all", "sadness_mean_all", "anger_mean_all",
    "fear_mean_all", "surprise_mean_all", "neutral_mean_all",
    "emotional_intensity_mean", "fear_variance", "joy_variance",
]
EMOTION_LABELS = ["喜悦", "悲伤", "愤怒", "恐惧", "惊讶", "中性"]
RANDOM_SEED = 42
MIN_CLUSTER_POSTS = int(os.getenv("MIN_CLUSTER_POSTS", "50"))
SAVE_MATPLOTLIB_PLOTS = os.getenv("SAVE_MATPLOTLIB_PLOTS", "0").strip().lower() in {"1", "true", "yes"}


def silhouette_score_safe(X, labels):
    """Pure Python silhouette score for small province matrices."""
    rows = [[float(v) for v in row] for row in X.tolist()]
    labels = [int(v) for v in labels]
    n = len(rows)
    if n < 3 or len(set(labels)) < 2:
        return 0.0

    distances = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = sqrt(sum((rows[i][c] - rows[j][c]) ** 2 for c in range(len(rows[i]))))
            distances[i][j] = d
            distances[j][i] = d

    scores = []
    label_set = sorted(set(labels))
    for i, label in enumerate(labels):
        same = [j for j, other in enumerate(labels) if other == label and j != i]
        a = sum(distances[i][j] for j in same) / len(same) if same else 0.0
        b_candidates = []
        for other_label in label_set:
            if other_label == label:
                continue
            members = [j for j, other in enumerate(labels) if other == other_label]
            if members:
                b_candidates.append(sum(distances[i][j] for j in members) / len(members))
        b = min(b_candidates) if b_candidates else 0.0
        denom = max(a, b)
        scores.append((b - a) / denom if denom else 0.0)
    return sum(scores) / len(scores)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    import argparse
    parser = argparse.ArgumentParser(description="Province Emotion Clustering")
    parser.add_argument("--vectors", type=str, default=None,
                        help="Province vectors CSV (default: data/processed/province_emotion_vectors.csv)")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory for analysis (default: analysis/)")
    parser.add_argument("--data-dir", type=str, default=None,
                        help="Data output directory (default: data/processed/)")
    parser.add_argument("--summary", type=str, default=None,
                        help="Summary output path")
    args = parser.parse_args()

    print("=" * 60)
    print("Script 06: Province Emotion Clustering")
    print("=" * 60)

    input_path = Path(args.vectors) if args.vectors else PROCESSED_DIR / "province_emotion_vectors.csv"
    if not input_path.is_absolute():
        input_path = ROOT / input_path
    analysis_dir = Path(args.output_dir) if args.output_dir else ANALYSIS_DIR
    if not analysis_dir.is_absolute():
        analysis_dir = ROOT / analysis_dir
    data_dir = Path(args.data_dir) if args.data_dir else PROCESSED_DIR
    if not data_dir.is_absolute():
        data_dir = ROOT / data_dir
    if not input_path.exists():
        print(f"[ERROR] province_emotion_vectors.csv not found. Run Script 04 first.")
        sys.exit(1)

    df = pd.read_csv(input_path, encoding="utf-8-sig")
    print(f"Loaded {len(df)} provinces")

    # Filter to provinces with sufficient data
    df = df[df["total_posts_all"] >= MIN_CLUSTER_POSTS].copy()
    print(f"  {len(df)} provinces with >= {MIN_CLUSTER_POSTS} posts")

    if len(df) < 3:
        print("[WARN] Not enough provinces after filtering for clustering.")
        print("Set MIN_CLUSTER_POSTS lower for smoke runs or use the full labeled dataset.")
        sys.exit(0)

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    cluster_dir = analysis_dir / "province_clustering"
    cluster_dir.mkdir(parents=True, exist_ok=True)

    # Prepare features
    available_features = [c for c in FEATURE_COLS if c in df.columns]
    X = df[available_features].fillna(0).values
    provinces = df["province"].tolist()

    # Standardize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 1. Hierarchical clustering dendrogram
    print("\n[1/3] Hierarchical clustering (Ward linkage)...")
    Z = linkage(X_scaled, method="ward", metric="euclidean")
    linkage_path = TMP_DIR / "06_hierarchical_linkage.csv"
    pd.DataFrame(Z, columns=["left", "right", "distance", "sample_count"]).to_csv(
        linkage_path, index=False, encoding="utf-8-sig"
    )
    print(f"  [OK] Linkage matrix: {linkage_path}")

    if SAVE_MATPLOTLIB_PLOTS:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from scipy.cluster.hierarchy import dendrogram

        fig, ax = plt.subplots(figsize=(14, 8))
        dendrogram(Z, labels=provinces, leaf_rotation=90, leaf_font_size=9,
                   color_threshold=0.7 * max(Z[:, 2]))
        ax.set_title("Province Emotion Profile - Hierarchical Clustering (Ward)")
        ax.set_ylabel("Distance")
        dendro_path = cluster_dir / "province_clustering_hierarchical.png"
        fig.savefig(dendro_path, dpi=150)
        plt.close(fig)
        print(f"  [OK] Dendrogram: {dendro_path}")
    else:
        print("  [SKIP] Matplotlib dendrogram disabled (set SAVE_MATPLOTLIB_PLOTS=1 to try it).")

    # 2. Agglomerative clustering silhouette analysis
    print("\n[2/3] Agglomerative silhouette analysis (K=2..6)...")
    max_k = min(7, len(df) - 1)
    if max_k < 3:
        max_k = len(df)
    silhouettes = []
    cluster_labels_by_k = {}
    for k in range(2, max_k):
        labels = AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(X_scaled)
        sil = silhouette_score_safe(X_scaled, labels)
        silhouettes.append({"k": k, "silhouette": sil})
        cluster_labels_by_k[k] = labels

    if not silhouettes:
        print("[WARN] Not enough provinces for silhouette analysis.")
        sys.exit(0)

    sil_df = pd.DataFrame(silhouettes)
    best_k = sil_df.sort_values("silhouette", ascending=False).iloc[0]["k"]
    print(f"  Best K by silhouette: {int(best_k)} (score={sil_df.sort_values('silhouette', ascending=False).iloc[0]['silhouette']:.4f})")

    if SAVE_MATPLOTLIB_PLOTS:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(sil_df["k"], sil_df["silhouette"], "o-", color="#4A90D9", markersize=8)
        ax.set_xlabel("Number of Clusters (K)")
        ax.set_ylabel("Silhouette Score")
        ax.set_title(f"Agglomerative Silhouette Analysis (best K={int(best_k)})")
        sil_path = cluster_dir / "province_clustering_silhouette.png"
        fig.savefig(sil_path, dpi=150)
        plt.close(fig)
        print(f"  [OK] Silhouette plot: {sil_path}")
    else:
        print("  [SKIP] Matplotlib silhouette plot disabled (scores are saved as CSV).")

    # 3. Generate cluster labels using optimal K
    print(f"\n[3/3] Assigning clusters (K={int(best_k)})...")
    best_labels = cluster_labels_by_k[int(best_k)]
    df["cluster_label"] = best_labels

    # Per-cluster summary
    cluster_summary = df.groupby("cluster_label").agg(
        province_count=("province", "count"),
        provinces=("province", lambda x: ", ".join(sorted(x))),
        **{f: (f, "mean") for f in available_features}
    ).reset_index()

    print("\nCluster profiles:")
    for _, row in cluster_summary.iterrows():
        print(f"  Cluster {int(row['cluster_label'])}: {int(row['province_count'])} provinces")
        print(f"    {row['provinces'][:100]}...")

    # Save labels
    label_df = df[["province", "total_posts_all", "cluster_label"]].copy()
    data_dir.mkdir(parents=True, exist_ok=True)
    label_df.to_csv(data_dir / "cluster_labels.csv", index=False, encoding="utf-8-sig")
    print(f"\n[OK] Cluster labels: {data_dir / 'cluster_labels.csv'}")

    # Save silhouette scores
    sil_df.to_csv(TMP_DIR / "06_silhouette_scores.csv", index=False, encoding="utf-8-sig")

    # Save stability matrix (province x K labels)
    stability = df[["province"]].copy()
    for k in sorted(cluster_labels_by_k.keys()):
        stability[f"k{k}"] = cluster_labels_by_k[k]
    stability.to_csv(TMP_DIR / "06_cluster_stability.csv", index=False, encoding="utf-8-sig")

    print("\nDone.")


if __name__ == "__main__":
    main()
