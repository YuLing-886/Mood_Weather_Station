import { EMOTION_COLORS, CLUSTER_COLORS } from "./theme";

export const EMOTIONS = ["joy", "sadness", "anger", "fear", "surprise", "neutral"] as const;

export type EmotionKey = (typeof EMOTIONS)[number];

export const EMOTION_META: Record<EmotionKey, { label: string; color: string; weather: string }> = {
  joy: { label: "喜悦", color: EMOTION_COLORS.joy, weather: "暖阳" },
  sadness: { label: "悲伤", color: EMOTION_COLORS.sadness, weather: "冷雨" },
  anger: { label: "愤怒", color: EMOTION_COLORS.anger, weather: "热浪" },
  fear: { label: "恐惧", color: EMOTION_COLORS.fear, weather: "低压" },
  surprise: { label: "惊讶", color: EMOTION_COLORS.surprise, weather: "闪电" },
  neutral: { label: "中性", color: EMOTION_COLORS.neutral, weather: "薄云" }
};

export { EMOTION_COLORS, CLUSTER_COLORS };

export const SEVERITY_ORDER: Record<string, number> = {
  extreme: 3,
  severe: 2,
  moderate: 1
};

export const LOW_SAMPLE_THRESHOLD = 10;

export const ASSET_BASE = import.meta.env.BASE_URL;

export function assetPath(path: string) {
  return `${ASSET_BASE}${path.replace(/^\/+/, "")}`;
}
