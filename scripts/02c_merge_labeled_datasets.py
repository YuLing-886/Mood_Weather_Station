"""
Script 02c: Merge Labeled Datasets
Merges existing labeled_dataset.csv with newly labeled stratified data.
Deduplicates by post_id, preferring label_status=ok records.
"""
import pandas as pd
import json
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
TMP_DIR = ROOT / "tmp"

EMOTION_KEYS = ["joy", "sadness", "anger", "fear", "surprise", "neutral"]


def compute_emotion_sum_valid(df):
    """Fraction of rows where 6 emotion scores sum to ~1.0."""
    if not all(k in df.columns for k in EMOTION_KEYS):
        return 0.0
    sums = df[EMOTION_KEYS].sum(axis=1)
    return round(float((abs(sums - 1.0) < 0.05).mean()), 4)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    import argparse

    parser = argparse.ArgumentParser(description="Merge labeled datasets")
    parser.add_argument("--old", type=str, default=None,
                        help="Path to existing labeled dataset")
    parser.add_argument("--new", type=str, default=None,
                        help="Path to newly labeled dataset")
    parser.add_argument("--output", type=str, default=None,
                        help="Output merged CSV path")
    parser.add_argument("--summary", type=str, default=None,
                        help="Output summary JSON path")
    args = parser.parse_args()

    # Resolve paths
    old_path = Path(args.old) if args.old else PROCESSED_DIR / "labeled_dataset.csv"
    new_path = Path(args.new) if args.new else PROCESSED_DIR / "labeled_dataset_stratified_new_cap30.csv"
    output_path = Path(args.output) if args.output else PROCESSED_DIR / "labeled_dataset_merged_cap30.csv"
    summary_path = Path(args.summary) if args.summary else TMP_DIR / "02c_merge_labeled_datasets_summary.json"

    if not old_path.is_absolute():
        old_path = ROOT / old_path
    if not new_path.is_absolute():
        new_path = ROOT / new_path
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    if not summary_path.is_absolute():
        summary_path = ROOT / summary_path

    print("=" * 60)
    print("Script 02c: Merge Labeled Datasets")
    print("=" * 60)

    # Ensure output dirs
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    # Load
    print(f"\n[1/5] Loading old dataset: {old_path}")
    if not old_path.exists():
        print(f"[ERROR] Old dataset not found: {old_path}")
        sys.exit(1)
    old_df = pd.read_csv(old_path, encoding="utf-8-sig")
    old_df["post_id"] = old_df["post_id"].astype(str)
    print(f"  Old rows: {len(old_df)}")

    print(f"\n[2/5] Loading new dataset: {new_path}")
    if not new_path.exists():
        print(f"[WARN] New dataset not found: {new_path}")
        print("  Copying old dataset as output (no new data to merge).")
        old_df.to_csv(output_path, index=False, encoding="utf-8-sig")
        summary = {
            "old_rows": len(old_df),
            "new_rows": 0,
            "merged_rows": len(old_df),
            "duplicate_post_ids": 0,
            "ok_rate": round(float((old_df["label_status"] == "ok").mean()), 4) if "label_status" in old_df.columns else 1.0,
            "emotion_sum_valid_rate": compute_emotion_sum_valid(old_df),
            "note": "New dataset not found; old dataset copied as-is.",
            "timestamp": datetime.now().isoformat(),
        }
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"  Output: {output_path}")
        print(f"  Summary: {summary_path}")
        return

    new_df = pd.read_csv(new_path, encoding="utf-8-sig")
    new_df["post_id"] = new_df["post_id"].astype(str)
    print(f"  New rows: {len(new_df)}")

    # Find duplicates
    old_ids = set(old_df["post_id"])
    new_ids = set(new_df["post_id"])
    overlap = old_ids & new_ids
    print(f"\n[3/5] Duplicate post_ids: {len(overlap)}")

    # Merge: concat, then dedup keeping ok status preferentially
    combined = pd.concat([old_df, new_df], ignore_index=True)

    if "label_status" in combined.columns:
        # Assign priority: ok=0, other=1 (so ok sorts first)
        combined["_merge_priority"] = (combined["label_status"] != "ok").astype(int)
        combined = combined.sort_values(["post_id", "_merge_priority"])
        combined = combined.drop_duplicates(subset=["post_id"], keep="first")
        combined = combined.drop(columns=["_merge_priority"])
    else:
        combined = combined.drop_duplicates(subset=["post_id"], keep="first")

    combined = combined.sort_values("post_id").reset_index(drop=True)

    print(f"\n[4/5] Merged rows: {len(combined)}")

    # Save
    combined.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"  Output: {output_path}")

    # Compute stats
    ok_count = (combined["label_status"] == "ok").sum() if "label_status" in combined.columns else len(combined)
    ok_rate = round(ok_count / len(combined), 4) if len(combined) > 0 else 0

    summary = {
        "old_rows": len(old_df),
        "new_rows": len(new_df),
        "merged_rows": len(combined),
        "duplicate_post_ids": len(overlap),
        "ok_rate": ok_rate,
        "emotion_sum_valid_rate": compute_emotion_sum_valid(combined),
        "timestamp": datetime.now().isoformat(),
    }

    print(f"\n[5/5] Saving summary...")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"  Summary: {summary_path}")

    print(f"\n{'=' * 60}")
    print(f"MERGE RESULTS")
    print(f"{'=' * 60}")
    print(f"  Old rows:         {summary['old_rows']}")
    print(f"  New rows:         {summary['new_rows']}")
    print(f"  Merged rows:      {summary['merged_rows']}")
    print(f"  Duplicates:       {summary['duplicate_post_ids']}")
    print(f"  OK rate:          {summary['ok_rate']}")
    print(f"  Emotion validity: {summary['emotion_sum_valid_rate']}")
    print(f"\nDone.")


if __name__ == "__main__":
    main()
