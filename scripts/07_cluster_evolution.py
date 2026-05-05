"""
Script 07: Cluster Evolution
Monthly independent clustering to track how provinces shift clusters over time.
Outputs: monthly cluster label matrices.
PNG heatmap is optional via SAVE_MATPLOTLIB_PLOTS=1.
"""
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import AgglomerativeClustering

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
ANALYSIS_DIR = ROOT / "analysis"
TMP_DIR = ROOT / "tmp"

FEATURE_COLS = ["joy_mean", "sadness_mean", "anger_mean", "fear_mean", "surprise_mean", "neutral_mean"]
N_CLUSTERS = 3
MIN_MONTHLY_CLUSTER_POSTS = int(os.getenv("MIN_MONTHLY_CLUSTER_POSTS", "20"))
SAVE_MATPLOTLIB_PLOTS = os.getenv("SAVE_MATPLOTLIB_PLOTS", "0").strip().lower() in {"1", "true", "yes"}


def align_monthly_labels(month_data, labels, available_features):
    """Remap independent monthly cluster ids to a stable low-to-high risk order."""
    tmp = month_data[available_features].copy()
    tmp["cluster_raw"] = labels
    centroids = tmp.groupby("cluster_raw")[available_features].mean()

    def risk_score(row):
        return (
            row.get("sadness_mean", 0)
            + row.get("anger_mean", 0)
            + row.get("fear_mean", 0)
            - row.get("joy_mean", 0)
        )

    ordered = centroids.apply(risk_score, axis=1).sort_values().index.tolist()
    remap = {old_label: new_label for new_label, old_label in enumerate(ordered)}
    return [remap[lbl] for lbl in labels]


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    import argparse
    parser = argparse.ArgumentParser(description="Cluster Evolution")
    parser.add_argument("--monthly", type=str, default=None,
                        help="Monthly panel CSV (default: data/processed/emotion_panel_monthly.csv)")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory for analysis (default: analysis/)")
    parser.add_argument("--tmp-dir", type=str, default=None,
                        help="Temp directory for labels CSV (default: tmp/)")
    parser.add_argument("--summary", type=str, default=None,
                        help="Summary output path")
    args = parser.parse_args()

    print("=" * 60)
    print("Script 07: Cluster Evolution")
    print("=" * 60)

    input_path = Path(args.monthly) if args.monthly else PROCESSED_DIR / "emotion_panel_monthly.csv"
    if not input_path.is_absolute():
        input_path = ROOT / input_path
    analysis_dir = Path(args.output_dir) if args.output_dir else ANALYSIS_DIR
    if not analysis_dir.is_absolute():
        analysis_dir = ROOT / analysis_dir
    tmp_dir = Path(args.tmp_dir) if args.tmp_dir else TMP_DIR
    if not tmp_dir.is_absolute():
        tmp_dir = ROOT / tmp_dir
    if not input_path.exists():
        print(f"[ERROR] emotion_panel_monthly.csv not found. Run Script 04 first.")
        sys.exit(1)

    df = pd.read_csv(input_path, encoding="utf-8-sig")
    print(f"Loaded {len(df)} rows, {df['date_month'].nunique()} months, {df['province'].nunique()} provinces")

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    evo_dir = analysis_dir / "temporal_cluster_evolution"
    evo_dir.mkdir(parents=True, exist_ok=True)

    # Filter reliable data
    df = df[df["total_posts"] >= MIN_MONTHLY_CLUSTER_POSTS].copy()

    # Cluster each month independently
    print(f"\nClustering each month independently (K={N_CLUSTERS})...")
    monthly_labels = {}
    all_provinces = sorted(df["province"].unique())
    months = sorted(df["date_month"].unique())

    for month in months:
        month_data = df[df["date_month"] == month].copy()
        present = set(month_data["province"].unique())

        if len(month_data) < N_CLUSTERS * 3:
            # Not enough data, assign all to cluster 0
            for p in present:
                monthly_labels.setdefault(p, {})[month] = 0
            continue

        available = [c for c in FEATURE_COLS if c in month_data.columns]
        X = month_data[available].fillna(0).values
        X_scaled = StandardScaler().fit_transform(X)

        labels = AgglomerativeClustering(n_clusters=N_CLUSTERS).fit_predict(X_scaled)
        labels = align_monthly_labels(month_data, labels, available)
        for p, lbl in zip(month_data["province"].tolist(), labels):
            monthly_labels.setdefault(p, {})[month] = lbl

    # Build evolution matrix
    evol_data = {}
    for province in all_provinces:
        evol_data[province] = {}
        for month in months:
            evol_data[province][month] = monthly_labels.get(province, {}).get(month, -1)

    evol_df = pd.DataFrame(evol_data).T
    evol_df = evol_df[months]  # ensure column order

    # Filter to provinces present in at least 6 months
    present_count = (evol_df >= 0).sum(axis=1)
    evol_df_filtered = evol_df[present_count >= 6]

    print(f"  Evolution matrix: {evol_df_filtered.shape[0]} provinces x {len(months)} months")

    # Save labels matrix
    evol_df.to_csv(tmp_dir / "07_monthly_cluster_labels.csv", encoding="utf-8-sig")
    print(f"  [OK] Monthly labels: {tmp_dir / '07_monthly_cluster_labels.csv'}")
    evol_df_filtered.to_csv(tmp_dir / "07_monthly_cluster_labels_filtered.csv", encoding="utf-8-sig")

    # Optional heatmap. Default is off because matplotlib.savefig() crashes on this Windows env.
    if SAVE_MATPLOTLIB_PLOTS:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import seaborn as sns

        fig, ax = plt.subplots(figsize=(16, 10))
        cmap = sns.color_palette("Set2", N_CLUSTERS)
        sns.heatmap(evol_df_filtered, cmap=cmap, annot=False, cbar_kws={"label": "Cluster"},
                    linewidths=0.5, linecolor="#333", xticklabels=True, yticklabels=True,
                    ax=ax)
        ax.set_title("Province Emotion Cluster Evolution (Monthly)")
        ax.set_xlabel("Month")
        ax.set_ylabel("Province")
        heatmap_path = evo_dir / "cluster_evolution_summary.png"
        fig.savefig(heatmap_path, dpi=150)
        plt.close(fig)
        print(f"  [OK] Evolution heatmap: {heatmap_path}")
    else:
        print("  [SKIP] Matplotlib evolution heatmap disabled (matrix is saved as CSV).")

    # Print cluster shifts
    shifts = []
    for province in evol_df_filtered.index:
        labels = evol_df_filtered.loc[province].values
        labels = [l for l in labels if l >= 0]
        if len(labels) >= 2:
            n_shifts = sum(1 for i in range(1, len(labels)) if labels[i] != labels[i-1])
            if n_shifts > 0:
                shifts.append({"province": province, "n_shifts": n_shifts, "n_months": len(labels)})

    if shifts:
        top_shifters = sorted(shifts, key=lambda x: x["n_shifts"], reverse=True)[:10]
        print("\nTop 10 provinces with most cluster shifts:")
        for s in top_shifters:
            print(f"  {s['province']}: {s['n_shifts']} shifts over {s['n_months']} months")

    print("\nDone.")


if __name__ == "__main__":
    main()
