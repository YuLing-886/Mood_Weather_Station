"""
Script 03: Emotion Labeling Validation
Compares DeepSeek labels against SMP2020 human annotations.
Outputs: analysis/emotion_validation/*.csv + tmp/03_accuracy_report.json.
PNG plotting is skipped in the default pipeline because matplotlib.savefig()
can crash with native 0xc06d007f on this Windows environment.
"""
import pandas as pd
import json
import sys
import re
import os
import time
from math import sqrt, isfinite
from pathlib import Path
from datetime import datetime
from sklearn.metrics import confusion_matrix, classification_report, f1_score
from snownlp import SnowNLP
from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
SMP2020_DIR = ROOT / "data" / "raw" / "SMP2020_EWECT"
ANALYSIS_DIR = ROOT / "analysis" / "emotion_validation"
TMP_DIR = ROOT / "tmp"
load_dotenv()

EMOTION_LABELS = ["喜悦", "悲伤", "愤怒", "恐惧", "惊讶", "中性"]
EMOTION_KEYS = ["joy", "sadness", "anger", "fear", "surprise", "neutral"]
EMOTION_LABELS_EN = EMOTION_KEYS
EMOTION_LABEL_MAP_EN = dict(zip(EMOTION_LABELS, EMOTION_LABELS_EN))
LABEL_MAP = {
    "happy": "喜悦", "angry": "愤怒", "sad": "悲伤",
    "fear": "恐惧", "surprise": "惊讶", "neutral": "中性"
}
LABEL_TO_IDX = {label: i for i, label in enumerate(EMOTION_LABELS)}
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip() or "deepseek-chat"
BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1").strip() or "https://api.deepseek.com/v1"
TEMPERATURE = float(os.getenv("DEEPSEEK_TEMPERATURE", "0"))
MAX_TOKENS = int(os.getenv("DEEPSEEK_MAX_TOKENS", "2000"))
BATCH_SIZE = int(os.getenv("DEEPSEEK_BATCH_SIZE", "30"))
PROMPT_VERSION = "v1"
client = None

SYSTEM_PROMPT = """你是中文社交媒体情绪分析专家。为每条微博输出6维情绪分数(0-1):
喜悦(joy)、悲伤(sadness)、愤怒(anger)、恐惧(fear)、惊讶(surprise)、中性(neutral)
6维之和=1.0，输出严格JSON数组。

标注要点:
- 反讽/阴阳怪气可能隐含愤怒
- emoji可作情绪信号 (😭=悲伤 😡=愤怒 😊=喜悦)
- "封城"≠恐惧,看上下文("封城也要加油"=正面)
- 纯事实报道=中性

返回格式:
[{"id":1,"joy":...,"sadness":...,"anger":...,"fear":...,"surprise":...,"neutral":...}, ...]"""


def load_smp2020(n=500):
    """Load SMP2020 eval labeled data (JSON array of {id, content, label})"""
    eval_path = SMP2020_DIR / "virus_eval_labeled.txt"
    raw = eval_path.read_text(encoding="utf-8-sig").strip()
    try:
        data = json.loads(raw)
        df = pd.DataFrame(data)
    except Exception:
        df = pd.read_csv(eval_path, sep="\t", encoding="utf-8-sig")
    df["label_cn"] = df["label"].map(LABEL_MAP)
    df = df.dropna(subset=["label_cn"])
    if len(df) > n:
        df = df.sample(n, random_state=42)
    return df


def load_deepseek_labels():
    """Load DeepSeek-labeled mini_dataset"""
    path = PROCESSED_DIR / "labeled_dataset.csv"
    if not path.exists():
        print(f"[ERROR] labeled_dataset.csv not found at {path}")
        print("Run Script 02 first (smoke mode is sufficient for validation).")
        sys.exit(1)
    return pd.read_csv(path, encoding="utf-8-sig")


def get_client():
    global client
    if client is not None:
        return client
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY not set. SMP2020 validation needs API calls unless cached labels exist."
        )
    client = OpenAI(api_key=api_key, base_url=BASE_URL)
    return client


def parse_batch_response(raw, expected_count):
    if not raw:
        return None
    raw = raw.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    match = re.search(r'\[.*\]', raw, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        return None
    if not isinstance(data, list) or len(data) != expected_count:
        return None
    return data


def validate_scores(item):
    for k in EMOTION_KEYS:
        v = item.get(k)
        if v is None or not (0 <= v <= 1):
            return False
    total = sum(item.get(k, 0) for k in EMOTION_KEYS)
    return abs(total - 1.0) <= 0.03


def label_batch(texts):
    numbered = "\n".join([f"[{i+1}] {t}" for i, t in enumerate(texts)])
    response = get_client().chat.completions.create(
        model=MODEL,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": numbered},
        ],
    )
    raw = response.choices[0].message.content
    return parse_batch_response(raw, len(texts)), response.usage, raw


def label_smp2020_with_deepseek(smp):
    """Label SMP2020 texts with checkpoint cache, then return merged labels."""
    cache_path = TMP_DIR / "03_smp_deepseek_labels.csv"
    existing = pd.DataFrame()
    existing_ids = set()
    if cache_path.exists():
        existing = pd.read_csv(cache_path, encoding="utf-8-sig")
        if "id" in existing.columns:
            existing["id"] = existing["id"].astype(str)
            existing_ids = set(existing["id"].tolist())
            print(f"  [Resume] Cached SMP labels: {len(existing_ids)}")

    rows = []
    usage_total = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    smp = smp.copy()
    smp["id"] = smp["id"].astype(str)

    for start in range(0, len(smp), BATCH_SIZE):
        batch = smp.iloc[start:start + BATCH_SIZE]
        batch = batch[~batch["id"].isin(existing_ids)]
        if batch.empty:
            continue

        texts = batch["content"].astype(str).tolist()
        success = False
        for attempt in range(3):
            parsed, usage, raw = label_batch(texts)
            if parsed is not None and all(validate_scores(item) for item in parsed):
                success = True
                break
            time.sleep(1)
        if not success:
            raise RuntimeError(f"DeepSeek validation batch failed near row {start}; raw={raw[:200] if raw else ''}")

        for (_, src_row), item in zip(batch.iterrows(), parsed):
            out = {
                "id": str(src_row["id"]),
                "content": src_row["content"],
                "label_true": src_row["label_cn"],
                "label_raw": src_row["label"],
            }
            for k in EMOTION_KEYS:
                out[k] = item.get(k, 0)
            rows.append(out)
            existing_ids.add(str(src_row["id"]))

        usage_total["prompt_tokens"] += usage.prompt_tokens
        usage_total["completion_tokens"] += usage.completion_tokens
        usage_total["total_tokens"] += usage.total_tokens
        pd.concat([existing, pd.DataFrame(rows)], ignore_index=True).drop_duplicates(
            subset=["id"], keep="last"
        ).to_csv(cache_path, index=False, encoding="utf-8-sig")
        print(f"  SMP validation progress: {len(existing_ids)}/{len(smp)}")
        time.sleep(0.3)

    if rows:
        labels = pd.concat([existing, pd.DataFrame(rows)], ignore_index=True)
        labels = labels.drop_duplicates(subset=["id"], keep="last")
    else:
        labels = existing

    return labels, usage_total


def predict_dominant(row):
    """Return dominant emotion label from 6-dim scores"""
    vals = {label: row.get(key, 0) for label, key in zip(EMOTION_LABELS, EMOTION_KEYS)}
    return max(vals, key=vals.get)


def positive_index(row):
    """Compute positive index for correlation with SnowNLP"""
    joy = row.get("joy", 0)
    surprise = row.get("surprise", 0)
    neutral = row.get("neutral", 0)
    return (joy + 0.5 * surprise) / (1 - neutral + 0.01)


def pearson_r_safe(xs, ys):
    """Pure Python Pearson r to avoid native crashes in numpy.corrcoef on Windows."""
    pairs = [(float(x), float(y)) for x, y in zip(xs, ys) if isfinite(float(x)) and isfinite(float(y))]
    if len(pairs) < 2:
        return None
    n = len(pairs)
    sum_x = sum(x for x, _ in pairs)
    sum_y = sum(y for _, y in pairs)
    mean_x = sum_x / n
    mean_y = sum_y / n
    diff_x = [x - mean_x for x, _ in pairs]
    diff_y = [y - mean_y for _, y in pairs]
    denom_x = sum(dx * dx for dx in diff_x)
    denom_y = sum(dy * dy for dy in diff_y)
    if denom_x <= 0 or denom_y <= 0:
        return None
    numer = sum(dx * dy for dx, dy in zip(diff_x, diff_y))
    return numer / sqrt(denom_x * denom_y)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-samples", type=int, default=500,
                        help="Number of SMP2020 samples to label for validation")
    args = parser.parse_args()

    print("=" * 60)
    print("Script 03: Emotion Labeling Validation")
    print(f"Model: {MODEL}, Base URL: {BASE_URL}, Temperature: {TEMPERATURE}, Batch: {BATCH_SIZE}")
    print("=" * 60)

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load SMP2020
    print("\n[1/4] Loading SMP2020 eval data...")
    smp = load_smp2020(args.max_samples)
    print(f"  Loaded {len(smp)} SMP2020 samples")
    print(f"  Label distribution: {smp['label_cn'].value_counts().to_dict()}")

    # 2. Label SMP2020 texts with DeepSeek and compute accuracy/F1
    print("\n[2/4] Labeling SMP2020 texts with DeepSeek / loading cache...")
    try:
        smp_labels, usage = label_smp2020_with_deepseek(smp)
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    smp_labels["predicted"] = smp_labels.apply(predict_dominant, axis=1)
    y_true = smp_labels["label_true"].tolist()
    y_pred = smp_labels["predicted"].tolist()
    cm = confusion_matrix(y_true, y_pred, labels=EMOTION_LABELS)
    report_dict = classification_report(
        y_true, y_pred, labels=EMOTION_LABELS, output_dict=True, zero_division=0
    )
    macro_f1 = f1_score(y_true, y_pred, labels=EMOTION_LABELS, average="macro", zero_division=0)
    micro_f1 = f1_score(y_true, y_pred, labels=EMOTION_LABELS, average="micro", zero_division=0)
    accuracy = report_dict.get("accuracy", 0.0)
    print(f"  Accuracy={accuracy:.4f}, macro_f1={macro_f1:.4f}, micro_f1={micro_f1:.4f}")

    # 3. Load project labels and compute SnowNLP comparison if available
    print("\n[3/4] Computing SnowNLP comparison on project labels...")
    snownlp_r = None
    labeled_count = 0
    dom_counts = {}
    emotion_means = {}
    emotion_stds = {}
    try:
        labeled = load_deepseek_labels()
        required = ["content_clean"] + EMOTION_KEYS
        missing = [c for c in required if c not in labeled.columns]
        if missing:
            raise ValueError(f"labeled_dataset.csv missing columns for SnowNLP comparison: {missing}")
        labeled_count = len(labeled)
        labeled["predicted"] = labeled.apply(predict_dominant, axis=1)
        labeled["positive_idx"] = labeled.apply(positive_index, axis=1)
        sample = labeled.head(min(2000, len(labeled))).copy()
        snownlp_scores = []
        for text in sample["content_clean"].head(500):
            try:
                snownlp_scores.append(SnowNLP(str(text)).sentiments)
            except Exception:
                snownlp_scores.append(0.5)
        sample_500 = sample.head(500).copy()
        sample_500["snownlp"] = snownlp_scores
        snownlp_r = pearson_r_safe(sample_500["snownlp"].tolist(), sample_500["positive_idx"].tolist())
        if snownlp_r is not None:
            snownlp_r = float(snownlp_r)
        dom_counts = labeled["predicted"].value_counts().to_dict()
        emotion_means = {k: round(float(labeled[k].mean()), 4) for k in EMOTION_KEYS}
        emotion_stds = {k: round(float(labeled[k].std()), 4) for k in EMOTION_KEYS}
    except SystemExit:
        print("  labeled_dataset.csv not found; skipping SnowNLP/project-label comparison.")
        labeled = pd.DataFrame()
        sample_500 = pd.DataFrame()
    except Exception as e:
        print(f"  [WARN] SnowNLP/project-label comparison skipped: {e}")
        labeled = pd.DataFrame()
        sample_500 = pd.DataFrame()

    # 4. Save validation tables. PNG plotting is intentionally skipped here:
    # on this Windows environment matplotlib.savefig() raises native 0xc06d007f.
    print("\n[4/4] Saving validation tables...")
    cm_path = ANALYSIS_DIR / "confusion_matrix.csv"
    pd.DataFrame(cm, index=EMOTION_LABELS, columns=EMOTION_LABELS).to_csv(cm_path, encoding="utf-8-sig")
    print(f"  [OK] Confusion matrix table: {cm_path}")

    if snownlp_r is not None and not sample_500.empty:
        scatter_path = ANALYSIS_DIR / "deepseek_vs_snownlp_sample.csv"
        keep_cols = ["content_clean", "snownlp", "positive_idx"] + EMOTION_KEYS
        sample_500[keep_cols].to_csv(scatter_path, index=False, encoding="utf-8-sig")
        print(f"  [OK] SnowNLP comparison sample: {scatter_path}")

    if not labeled.empty:
        dist_path = ANALYSIS_DIR / "emotion_distribution_summary.csv"
        pd.DataFrame({
            "emotion": EMOTION_KEYS,
            "mean": [emotion_means.get(k) for k in EMOTION_KEYS],
            "std": [emotion_stds.get(k) for k in EMOTION_KEYS],
        }).to_csv(dist_path, index=False, encoding="utf-8-sig")
        print(f"  [OK] Emotion distribution summary: {dist_path}")

    if dom_counts:
        dom_path = ANALYSIS_DIR / "dominant_emotion_distribution.csv"
        pd.Series(dom_counts, name="count").rename_axis("dominant_emotion").reset_index().to_csv(
            dom_path, index=False, encoding="utf-8-sig"
        )
        print(f"  [OK] Dominant emotion table: {dom_path}")

    # Save accuracy report
    report = {
        "smp2020_sample_count": len(smp_labels),
        "accuracy": round(float(accuracy), 4),
        "macro_f1": round(float(macro_f1), 4),
        "micro_f1": round(float(micro_f1), 4),
        "classification_report": report_dict,
        "snownlp_pearson_r": round(float(snownlp_r), 4) if snownlp_r is not None else None,
        "deepseek_labeled_count": labeled_count,
        "dominant_emotion_distribution": dom_counts,
        "emotion_means": emotion_means,
        "emotion_stds": emotion_stds,
        "usage": usage,
        "model": MODEL,
        "base_url": BASE_URL,
        "prompt_version": PROMPT_VERSION,
        "timestamp": datetime.now().isoformat(),
        "notes": [
            "SMP2020 accuracy/F1 is computed by labeling SMP2020 texts with the same DeepSeek prompt",
            "SnowNLP correlation is a secondary sanity check, not the primary accuracy metric"
        ]
    }
    report_path = TMP_DIR / "03_accuracy_report.json"
    json.dump(report, open(report_path, "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print(f"  [OK] Accuracy report: {report_path}")

    print(f"\nDone. Accuracy={accuracy:.4f}, macro_f1={macro_f1:.4f}")
    return report


if __name__ == "__main__":
    main()
