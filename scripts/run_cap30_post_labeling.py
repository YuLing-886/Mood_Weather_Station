"""
Post-cap30-labeling pipeline: quality report, merge, re-run 04-08, summaries.
Run with: python scripts/run_cap30_post_labeling.py
"""
import pandas as pd
import numpy as np
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
TMP_DIR = ROOT / "tmp"

EMOTION_KEYS = ["joy", "sadness", "anger", "fear", "surprise", "neutral"]
VALID_PROVINCES = {
    "北京", "天津", "上海", "重庆", "河北", "山西", "辽宁", "吉林", "黑龙江",
    "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北", "湖南",
    "广东", "广西", "海南", "四川", "贵州", "云南", "西藏", "陕西", "甘肃",
    "青海", "宁夏", "新疆", "内蒙古", "香港", "澳门", "台湾",
}
PYTHON = r"D:\anaconda\envs\py312\python.exe"


def run_script(script, args=None):
    """Run a Python script and return exit code."""
    cmd = [PYTHON, str(ROOT / script)]
    if args:
        cmd.extend(args)
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, cwd=str(ROOT), capture_output=False)
    return result.returncode


def generate_cap30_quality_report():
    """Generate quality report for cap30 labeled data."""
    output_path = PROCESSED_DIR / "labeled_dataset_stratified_new_cap30.csv"
    plan_path = PROCESSED_DIR / "stratified_label_plan_cap30.csv"

    if not output_path.exists():
        print("[ERROR] cap30 labeled output not found")
        return None

    df = pd.read_csv(output_path, encoding="utf-8-sig")
    plan_df = pd.read_csv(plan_path, encoding="utf-8-sig") if plan_path.exists() else None

    report = {
        "generated_at": datetime.now().isoformat(),
        "rows": len(df),
        "expected_rows": len(plan_df) if plan_df is not None else "unknown",
        "label_status_distribution": df["label_status"].value_counts().to_dict() if "label_status" in df.columns else {},
        "ok_rate": round(float((df["label_status"] == "ok").mean()), 4) if "label_status" in df.columns else 0,
        "emotion_sum_valid_rate": round(float((abs(df[EMOTION_KEYS].sum(axis=1) - 1.0) < 0.05).mean()), 4),
        "all_dims_in_range_rate": round(float(
            ((df[EMOTION_KEYS] >= 0) & (df[EMOTION_KEYS] <= 1)).all(axis=1).mean()
        ), 4),
        "duplicate_post_ids": int(df["post_id"].duplicated().sum()),
        "empty_content_clean": int((df["content_clean"].str.strip() == "").sum()) if "content_clean" in df.columns else 0,
        "invalid_province_count": int((~df["province"].isin(VALID_PROVINCES)).sum()) if "province" in df.columns else 0,
        "dominant_emotion_distribution": df[EMOTION_KEYS].idxmax(axis=1).value_counts().to_dict(),
        "emotion_means": {k: round(float(df[k].mean()), 4) for k in EMOTION_KEYS},
        "neutral_1_count": int((df["neutral"] >= 0.99).sum()),
        "neutral_1_ratio": round(float((df["neutral"] >= 0.99).mean()), 4),
        "fear_dominant_count": int((df[EMOTION_KEYS].idxmax(axis=1) == "fear").sum()),
        "fear_dominant_ratio": round(float((df[EMOTION_KEYS].idxmax(axis=1) == "fear").mean()), 4),
    }

    # Try to read token usage from log
    log_path = TMP_DIR / "02_labeling_log.json"
    if log_path.exists():
        with open(log_path, "r", encoding="utf-8") as f:
            log = json.load(f)
        report["total_tokens_if_available"] = log.get("usage", {}).get("total_tokens", "N/A")
        report["total_batches_if_available"] = log.get("total_batches", "N/A")

    report_path = TMP_DIR / "02_cap30_labeling_quality_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n[Quality Report]")
    for k, v in report.items():
        if k != "generated_at":
            print(f"  {k}: {v}")

    return report


def generate_merge_summary():
    """Read and display merge summary."""
    summary_path = TMP_DIR / "02c_merge_labeled_datasets_cap30_summary.json"
    if not summary_path.exists():
        print("[WARN] Merge summary not found")
        return
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)
    print(f"\n[Merge Summary]")
    for k, v in summary.items():
        if k != "timestamp":
            print(f"  {k}: {v}")


def generate_aggregation_summary():
    """Read and display aggregation summary."""
    summary_path = TMP_DIR / "04_aggregation_summary.txt"
    if not summary_path.exists():
        print("[WARN] Aggregation summary not found")
        return
    print(f"\n[Aggregation Summary]")
    with open(summary_path, "r", encoding="utf-8") as f:
        print(f.read())


def generate_anomaly_summary():
    """Generate anomaly detection summary."""
    anom_path = PROCESSED_DIR / "anomaly_detection.json"
    if not anom_path.exists():
        print("[WARN] Anomaly detection not found")
        return

    with open(anom_path, "r", encoding="utf-8") as f:
        anomalies = json.load(f)

    summary = {
        "anomaly_count": len(anomalies),
        "empty_top_provinces": sum(1 for a in anomalies if not a.get("top_provinces")),
        "has_top_provinces_reason": sum(1 for a in anomalies if "top_provinces_reason" in a),
        "severity_distribution": {},
        "emotion_distribution": {},
    }

    for a in anomalies:
        sev = a.get("severity", "unknown")
        emo = a.get("emotion", "unknown")
        summary["severity_distribution"][sev] = summary["severity_distribution"].get(sev, 0) + 1
        summary["emotion_distribution"][emo] = summary["emotion_distribution"].get(emo, 0) + 1

    summary_path = TMP_DIR / "05_anomaly_detection_cap30_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n[Anomaly Summary]")
    for k, v in summary.items():
        print(f"  {k}: {v}")


def generate_cluster_summary():
    """Generate clustering summary."""
    vectors_path = PROCESSED_DIR / "province_emotion_vectors.csv"
    labels_path = PROCESSED_DIR / "cluster_labels.csv"

    if not vectors_path.exists() or not labels_path.exists():
        print("[WARN] Clustering files not found")
        return

    vectors = pd.read_csv(vectors_path, encoding="utf-8-sig")
    labels = pd.read_csv(labels_path, encoding="utf-8-sig")

    sil_path = TMP_DIR / "06_silhouette_scores.csv"
    best_k = "N/A"
    best_sil = "N/A"
    if sil_path.exists():
        sil_df = pd.read_csv(sil_path, encoding="utf-8-sig")
        if len(sil_df) > 0:
            best_row = sil_df.sort_values("silhouette", ascending=False).iloc[0]
            best_k = int(best_row["k"])
            best_sil = round(float(best_row["silhouette"]), 4)

    summary = {
        "total_provinces_in_vectors": len(vectors),
        "provinces_with_ge50_posts": int((vectors["total_posts_all"] >= 50).sum()),
        "provinces_with_ge30_posts": int((vectors["total_posts_all"] >= 30).sum()),
        "clustered_provinces": len(labels),
        "num_clusters": int(labels["cluster_label"].nunique()) if len(labels) > 0 else 0,
        "best_k": best_k,
        "silhouette_score": best_sil,
        "coverage_pct": round(len(labels) / 34 * 100, 1),
    }

    summary_path = TMP_DIR / "06_cluster_summary_cap30.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n[Cluster Summary]")
    for k, v in summary.items():
        print(f"  {k}: {v}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("CAP30 Post-Labeling Pipeline")
    print("=" * 60)

    # Step 1: Quality report
    print("\n[STEP 1] Generating cap30 quality report...")
    report = generate_cap30_quality_report()
    if report is None:
        print("[ERROR] Cannot proceed without cap30 output")
        sys.exit(1)

    if report["ok_rate"] < 0.99:
        print(f"[ERROR] ok_rate={report['ok_rate']} < 0.99. Stopping.")
        sys.exit(1)
    if report["emotion_sum_valid_rate"] < 0.99:
        print(f"[ERROR] emotion_sum_valid_rate={report['emotion_sum_valid_rate']} < 0.99. Stopping.")
        sys.exit(1)

    # Step 2: Merge
    print("\n[STEP 2] Merging datasets...")
    rc = run_script("scripts/02c_merge_labeled_datasets.py", [
        "--old", "data/processed/labeled_dataset.csv",
        "--new", "data/processed/labeled_dataset_stratified_new_cap30.csv",
        "--output", "data/processed/labeled_dataset_merged_cap30.csv",
        "--summary", "tmp/02c_merge_labeled_datasets_cap30_summary.json",
    ])
    if rc != 0:
        print(f"[ERROR] Merge failed with exit code {rc}")
        sys.exit(1)
    generate_merge_summary()

    # Step 3: Aggregate (04)
    print("\n[STEP 3] Running aggregation...")
    rc = run_script("scripts/04_aggregate_emotions.py", [
        "--input", "data/processed/labeled_dataset_merged_cap30.csv",
    ])
    if rc != 0:
        print(f"[ERROR] Aggregation failed with exit code {rc}")
        sys.exit(1)
    generate_aggregation_summary()

    # Step 4: Anomaly detection (05)
    print("\n[STEP 4] Running anomaly detection...")
    rc = run_script("scripts/05_detect_anomalies.py")
    if rc != 0:
        print(f"[ERROR] Anomaly detection failed with exit code {rc}")
        sys.exit(1)
    generate_anomaly_summary()

    # Step 5: Province clustering (06)
    print("\n[STEP 5] Running province clustering...")
    rc = run_script("scripts/06_cluster_provinces.py")
    if rc != 0:
        print(f"[ERROR] Clustering failed with exit code {rc}")
        sys.exit(1)

    # Step 6: Cluster evolution (07)
    print("\n[STEP 6] Running cluster evolution...")
    rc = run_script("scripts/07_cluster_evolution.py")
    if rc != 0:
        print(f"[ERROR] Cluster evolution failed with exit code {rc}")
        sys.exit(1)
    generate_cluster_summary()

    # Step 7: Frontend assets (08)
    print("\n[STEP 7] Exporting frontend assets...")
    rc = run_script("scripts/08_prepare_frontend_assets.py")
    if rc != 0:
        print(f"[ERROR] Frontend export failed with exit code {rc}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("CAP30 POST-LABELING PIPELINE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
