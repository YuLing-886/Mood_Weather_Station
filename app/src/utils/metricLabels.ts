/** Human-friendly labels for technical metrics */
export const METRIC_LABELS: Record<string, { label: string; description: string }> = {
  macro_f1: { label: "标注可信度", description: "情绪标注与人工标注的一致程度，越高越可靠" },
  z_score: { label: "异常强度", description: "当前值偏离历史均值的程度，绝对值越大越异常" },
  silhouette: { label: "分组清晰度", description: "省份聚类的分离程度，越高说明分组越明确" },
  positive_index: { label: "积极情绪相对强度", description: "积极情绪在非中性情绪中的占比" },
  reliable: { label: "样本充足度", description: "该省份/时间段的帖子数量是否足够支撑统计结论" },
  emotional_intensity: { label: "情绪温度", description: "非中性情绪的综合强度，越高说明情绪越激烈" },
  fear_joy_ratio: { label: "恐惧-喜悦比", description: "恐惧情绪与喜悦情绪的比值，>1 表示偏焦虑" },
  dominant_score: { label: "主导情绪强度", description: "当期最突出情绪的得分" }
};

/** Map a severity level to human text */
export function severityLabel(severity: string): string {
  switch (severity) {
    case "extreme":
      return "极端异常";
    case "severe":
      return "强烈异常";
    case "moderate":
      return "轻微异常";
    default:
      return severity;
  }
}

/** Map z-score to a human-readable intensity description */
export function zScoreDescription(z: number): string {
  const abs = Math.abs(z);
  if (abs >= 4) return "极端异常";
  if (abs >= 3) return "强烈异常";
  if (abs >= 2.5) return "明显偏高";
  return "轻微波动";
}

/** Format deviation percentage as human text */
export function deviationDescription(deviationPct: string): string {
  const match = deviationPct.match(/([+-]?\d+(\.\d+)?)/);
  if (!match) return deviationPct;
  const pct = parseFloat(match[1]);
  if (pct > 0) {
    return `比过去 4 周高出 ${Math.abs(pct).toFixed(0)}%`;
  }
  return `比过去 4 周低 ${Math.abs(pct).toFixed(0)}%`;
}

/** Cluster interpretation labels */
export const CLUSTER_INTERPRETATIONS: Record<string, { name: string; description: string }> = {
  "0": { name: "高情绪强度型", description: "情绪波动大，积极和消极情绪均较强，多为人口密集或事件敏感省份" },
  "1": { name: "稳定中性型", description: "情绪以中性为主，波动较小，整体情绪平稳" },
  "2": { name: "积极恢复型", description: "积极情绪占比较高，显示出较好的情绪恢复态势" },
  "3": { name: "高焦虑型", description: "恐惧和悲伤情绪偏高，可能受疫情冲击较大" },
  "4": { name: "情绪波动型", description: "情绪在不同时期变化剧烈，主导情绪频繁切换" },
  "5": { name: "低表达型", description: "整体情绪得分偏低，表达强度较弱" }
};

/** Get cluster interpretation, with fallback for unknown cluster IDs */
export function clusterInterpretation(clusterId: number): { name: string; description: string } {
  return CLUSTER_INTERPRETATIONS[String(clusterId)] ?? {
    name: `Cluster ${clusterId}`,
    description: "该聚类的特征描述暂不可用"
  };
}

/** Friendly label lookup */
export function friendlyLabel(key: string): string {
  return METRIC_LABELS[key]?.label ?? key;
}

/** Friendly description lookup */
export function friendlyDescription(key: string): string {
  return METRIC_LABELS[key]?.description ?? "";
}
