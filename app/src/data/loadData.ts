import Papa from "papaparse";
import { assetPath, EMOTIONS, type EmotionKey } from "../config";
import type {
  AnomalyEvent,
  ClusterLabel,
  DataBundle,
  MonthlyClusterMatrix,
  NationalWeek,
  PostExamplesPayload,
  ProvinceMonth,
  ProvinceVector,
  ProvinceWeek
} from "../types";
import { normalizeProvinceName } from "../utils/province";

type CsvRow = Record<string, string>;

let cache: Promise<DataBundle> | null = null;

function toNumber(value: unknown) {
  const n = Number.parseFloat(String(value ?? "").trim());
  return Number.isFinite(n) ? n : 0;
}

function toBool(value: unknown) {
  return String(value ?? "").toLowerCase() === "true";
}

function toEmotion(value: unknown): EmotionKey {
  const key = String(value ?? "neutral").trim() as EmotionKey;
  return EMOTIONS.includes(key) ? key : "neutral";
}

async function fetchText(path: string) {
  const response = await fetch(assetPath(path));
  if (!response.ok) {
    throw new Error(`Failed to fetch ${path}: ${response.status}`);
  }
  return response.text();
}

async function fetchJson<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(assetPath(path));
    if (!response.ok) return fallback;
    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

async function fetchCsv(path: string): Promise<CsvRow[]> {
  const text = await fetchText(path);
  const parsed = Papa.parse<CsvRow>(text, {
    header: true,
    skipEmptyLines: true,
    transformHeader: (header) => header.trim()
  });
  if (parsed.errors.length) {
    console.warn(`CSV parse warnings for ${path}`, parsed.errors);
  }
  return parsed.data.filter((row) => Object.values(row).some((value) => String(value ?? "").trim()));
}

function emotionMeans(row: CsvRow) {
  return {
    joy_mean: toNumber(row.joy_mean),
    sadness_mean: toNumber(row.sadness_mean),
    anger_mean: toNumber(row.anger_mean),
    fear_mean: toNumber(row.fear_mean),
    surprise_mean: toNumber(row.surprise_mean),
    neutral_mean: toNumber(row.neutral_mean)
  };
}

function parseNational(rows: CsvRow[]): NationalWeek[] {
  return rows.map((row) => ({
    date_week: row.date_week,
    total_posts: toNumber(row.total_posts),
    emotional_intensity: toNumber(row.emotional_intensity),
    dominant_emotion_key: toEmotion(row.dominant_emotion_key),
    dominant_emotion: row.dominant_emotion || "中性",
    positive_index: toNumber(row.positive_index),
    fear_joy_ratio: toNumber(row.fear_joy_ratio),
    ...emotionMeans(row)
  }));
}

function parseProvinceWeeks(rows: CsvRow[]): ProvinceWeek[] {
  return rows.map((row) => ({
    date_week: row.date_week,
    province: normalizeProvinceName(row.province),
    total_posts: toNumber(row.total_posts),
    avg_word_count: toNumber(row.avg_word_count),
    dominant_emotion_key: toEmotion(row.dominant_emotion_key),
    dominant_emotion: row.dominant_emotion || "中性",
    dominant_score: toNumber(row.dominant_score),
    positive_index: toNumber(row.positive_index),
    emotional_intensity: toNumber(row.emotional_intensity),
    fear_joy_ratio: toNumber(row.fear_joy_ratio),
    reliable: toBool(row.reliable),
    ...emotionMeans(row)
  }));
}

function parseProvinceMonths(rows: CsvRow[]): ProvinceMonth[] {
  return rows.map((row) => ({
    date_month: row.date_month,
    province: normalizeProvinceName(row.province),
    total_posts: toNumber(row.total_posts),
    emotional_intensity: toNumber(row.emotional_intensity),
    dominant_emotion_key: toEmotion(row.dominant_emotion_key),
    dominant_emotion: row.dominant_emotion || "中性",
    dominant_score: toNumber(row.dominant_score),
    reliable: toBool(row.reliable),
    ...emotionMeans(row)
  }));
}

function parseProvinceVectors(rows: CsvRow[], labels: ClusterLabel[]): ProvinceVector[] {
  const labelByProvince = new Map(labels.map((row) => [row.province, row.cluster_label]));
  return rows.map((row) => {
    const province = normalizeProvinceName(row.province);
    return {
      province,
      total_posts_all: toNumber(row.total_posts_all),
      joy_mean_all: toNumber(row.joy_mean_all),
      sadness_mean_all: toNumber(row.sadness_mean_all),
      anger_mean_all: toNumber(row.anger_mean_all),
      fear_mean_all: toNumber(row.fear_mean_all),
      surprise_mean_all: toNumber(row.surprise_mean_all),
      neutral_mean_all: toNumber(row.neutral_mean_all),
      emotional_intensity_mean: toNumber(row.emotional_intensity_mean),
      fear_variance: toNumber(row.fear_variance),
      joy_variance: toNumber(row.joy_variance),
      cluster_label: labelByProvince.get(province)
    };
  });
}

function parseClusterLabels(rows: CsvRow[]): ClusterLabel[] {
  return rows.map((row) => ({
    province: normalizeProvinceName(row.province),
    total_posts_all: toNumber(row.total_posts_all),
    cluster_label: Math.trunc(toNumber(row.cluster_label))
  }));
}

function parseMonthlyClusters(rows: CsvRow[]): MonthlyClusterMatrix {
  if (!rows.length) return { months: [], rows: [] };
  const keys = Object.keys(rows[0]);
  const provinceKey = keys.find((key) => !key || key.toLowerCase() === "province") ?? keys[0];
  const months = keys.filter((key) => key !== provinceKey && key.trim());
  return {
    months,
    rows: rows.map((row) => ({
      province: normalizeProvinceName(row[provinceKey]),
      values: months.map((month) => Math.trunc(toNumber(row[month])))
    }))
  };
}

function normalizePostExamples(payload: PostExamplesPayload): PostExamplesPayload {
  const provinces: PostExamplesPayload["provinces"] = {};
  for (const [province, byEmotion] of Object.entries(payload.provinces ?? {})) {
    provinces[normalizeProvinceName(province)] = byEmotion;
  }
  return {
    generated_at: payload.generated_at ?? "",
    source: payload.source,
    emotions: payload.emotions ?? [...EMOTIONS],
    provinces
  };
}

export function loadMoodData() {
  cache ??= loadMoodDataInner();
  return cache;
}

async function loadMoodDataInner(): Promise<DataBundle> {
  const [
    nationalRows,
    weekRows,
    monthRows,
    clusterRows,
    vectorRows,
    monthlyRows,
    anomalies,
    postExamples,
    chinaGeoJson
  ] = await Promise.all([
    fetchCsv("data/processed/emotion_national_timeline.csv").catch((e) => { throw new Error(`加载全国时序失败: ${e}`); }),
    fetchCsv("data/processed/emotion_panel_weekly.csv").catch((e) => { throw new Error(`加载周面板失败: ${e}`); }),
    fetchCsv("data/processed/emotion_panel_monthly.csv").catch((e) => { throw new Error(`加载月面板失败: ${e}`); }),
    fetchCsv("data/processed/cluster_labels.csv").catch((e) => { throw new Error(`加载聚类标签失败: ${e}`); }),
    fetchCsv("data/processed/province_emotion_vectors.csv").catch((e) => { throw new Error(`加载省份向量失败: ${e}`); }),
    fetchCsv("data/processed/monthly_cluster_labels.csv").catch((e) => { throw new Error(`加载月度聚类失败: ${e}`); }),
    fetchJson<AnomalyEvent[]>("data/processed/anomaly_detection.json", []),
    fetchJson<PostExamplesPayload>("data/processed/post_examples.json", {
      generated_at: "",
      emotions: [...EMOTIONS],
      provinces: {}
    }),
    fetchJson<unknown>("data/geo/china.json", null)
  ]);

  const clusterLabels = parseClusterLabels(clusterRows);
  return {
    nationalWeeks: parseNational(nationalRows),
    provinceWeeks: parseProvinceWeeks(weekRows),
    provinceMonths: parseProvinceMonths(monthRows),
    clusterLabels,
    provinceVectors: parseProvinceVectors(vectorRows, clusterLabels),
    monthlyClusters: parseMonthlyClusters(monthlyRows),
    anomalies: anomalies ?? [],
    postExamples: normalizePostExamples(postExamples),
    chinaGeoJson
  };
}
