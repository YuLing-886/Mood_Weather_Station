/**
 * Theme System — Mood Weather Station
 * 3 switchable presets driven by CSS variables.
 */

export type ThemePreset = "warmIvory" | "paperBeige" | "softDataBlue";

export interface ThemeTokens {
  bg: string;
  bgSoft: string;
  surface: string;
  surfaceSolid: string;
  surfaceWarm: string;
  border: string;
  borderStrong: string;
  text: string;
  textSecondary: string;
  textMuted: string;
  accent: string;
  accentSoft: string;
  accentDeep: string;
  shadow: string;
  shadowSoft: string;
  heroGradient: string;
  gridOverlay: string;
}

const warmIvory: ThemeTokens = {
  bg: "#F8F4EE",
  bgSoft: "#FBF9F5",
  surface: "rgba(255, 253, 249, 0.90)",
  surfaceSolid: "#FFFDF9",
  surfaceWarm: "#F5EDE2",
  border: "rgba(100, 72, 40, 0.10)",
  borderStrong: "rgba(100, 72, 40, 0.18)",
  text: "#1D1916",
  textSecondary: "#6B5D50",
  textMuted: "#9C8E80",
  accent: "#E07A3A",
  accentSoft: "#FFE0C4",
  accentDeep: "#B85C32",
  shadow: "0 20px 48px rgba(80, 50, 20, 0.08)",
  shadowSoft: "0 12px 32px rgba(80, 50, 20, 0.06)",
  heroGradient: "linear-gradient(135deg, rgba(224, 122, 58, 0.12), rgba(245, 237, 226, 0.4))",
  gridOverlay: `
    radial-gradient(circle at 20% 10%, rgba(224, 122, 58, 0.06), transparent 35%),
    radial-gradient(circle at 80% 50%, rgba(184, 92, 50, 0.04), transparent 30%)
  `
};

const paperBeige: ThemeTokens = {
  bg: "#F7F5F1",
  bgSoft: "#FAF8F5",
  surface: "rgba(252, 251, 248, 0.92)",
  surfaceSolid: "#FCFBF8",
  surfaceWarm: "#F0EBE3",
  border: "rgba(90, 75, 55, 0.10)",
  borderStrong: "rgba(90, 75, 55, 0.18)",
  text: "#24201C",
  textSecondary: "#635A4E",
  textMuted: "#938878",
  accent: "#C47D3E",
  accentSoft: "#F5DFC4",
  accentDeep: "#9E6430",
  shadow: "0 18px 44px rgba(70, 50, 25, 0.07)",
  shadowSoft: "0 10px 28px rgba(70, 50, 25, 0.05)",
  heroGradient: "linear-gradient(135deg, rgba(196, 125, 62, 0.10), rgba(240, 235, 227, 0.35))",
  gridOverlay: `
    radial-gradient(circle at 25% 5%, rgba(196, 125, 62, 0.05), transparent 32%),
    radial-gradient(circle at 75% 60%, rgba(158, 100, 48, 0.03), transparent 28%)
  `
};

const softDataBlue: ThemeTokens = {
  bg: "#F4F6F8",
  bgSoft: "#F8FAFB",
  surface: "rgba(255, 255, 255, 0.95)",
  surfaceSolid: "#FFFFFF",
  surfaceWarm: "#EDF1F5",
  border: "rgba(60, 80, 110, 0.10)",
  borderStrong: "rgba(60, 80, 110, 0.18)",
  text: "#1A2332",
  textSecondary: "#5A6B7E",
  textMuted: "#8A98A8",
  accent: "#3B7DD8",
  accentSoft: "#D6E6F9",
  accentDeep: "#2A5EA8",
  shadow: "0 18px 44px rgba(30, 50, 80, 0.07)",
  shadowSoft: "0 10px 28px rgba(30, 50, 80, 0.05)",
  heroGradient: "linear-gradient(135deg, rgba(59, 125, 216, 0.08), rgba(214, 230, 249, 0.3))",
  gridOverlay: `
    radial-gradient(circle at 20% 10%, rgba(59, 125, 216, 0.05), transparent 35%),
    radial-gradient(circle at 80% 50%, rgba(42, 94, 168, 0.03), transparent 30%)
  `
};

export const THEMES: Record<ThemePreset, ThemeTokens> = {
  warmIvory,
  paperBeige,
  softDataBlue
};

export const THEME_META: Record<ThemePreset, { label: string; sub: string; description: string }> = {
  warmIvory: { label: "Warm Ivory", sub: "暖象牙", description: "Apple 风格，留白更多，层次清爽" },
  paperBeige: { label: "Paper Beige", sub: "纸米色", description: "Notion 风格，像纸张和知识产品" },
  softDataBlue: { label: "Soft Data Blue", sub: "数据蓝", description: "数据产品风格，像分析平台" }
};

export const DEFAULT_THEME: ThemePreset = "softDataBlue";

/** Emotion palette — shared across all themes */
export const EMOTION_COLORS = {
  joy: "#F2A23A",
  sadness: "#5F8FA8",
  anger: "#D95C4A",
  fear: "#7D6AAE",
  surprise: "#E7C84F",
  neutral: "#A79A8D"
} as const;

/** Cluster palette */
export const CLUSTER_COLORS = [
  "#F2A23A",
  "#5F8FA8",
  "#7D6AAE",
  "#D95C4A",
  "#E7C84F",
  "#A79A8D"
] as const;

/** Map gradient */
export const MAP_GRADIENT = {
  noData: "#E6DDD2",
  low: "#F7E6CF",
  mid: "#F3BE7A",
  high: "#E9844A",
  extreme: "#C95F3D",
  stroke: "rgba(120, 82, 45, 0.38)"
} as const;

/** Read a CSS variable from :root as a concrete color string (for ECharts canvas) */
export function cssVar(name: string, fallback = ""): string {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v || fallback;
}

/** Apply theme tokens as CSS variables on :root */
export function applyTheme(preset: ThemePreset) {
  const t = THEMES[preset];
  const root = document.documentElement;
  root.style.setProperty("--bg", t.bg);
  root.style.setProperty("--bg-soft", t.bgSoft);
  root.style.setProperty("--surface", t.surface);
  root.style.setProperty("--surface-solid", t.surfaceSolid);
  root.style.setProperty("--surface-warm", t.surfaceWarm);
  root.style.setProperty("--border", t.border);
  root.style.setProperty("--border-strong", t.borderStrong);
  root.style.setProperty("--text", t.text);
  root.style.setProperty("--text-secondary", t.textSecondary);
  root.style.setProperty("--text-muted", t.textMuted);
  root.style.setProperty("--accent", t.accent);
  root.style.setProperty("--accent-soft", t.accentSoft);
  root.style.setProperty("--accent-deep", t.accentDeep);
  root.style.setProperty("--shadow", t.shadow);
  root.style.setProperty("--shadow-soft", t.shadowSoft);
  root.style.setProperty("--hero-gradient", t.heroGradient);
  root.style.setProperty("--grid-overlay", t.gridOverlay);
  root.setAttribute("data-theme", preset);
}
