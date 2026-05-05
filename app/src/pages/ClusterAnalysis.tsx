import { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { ChartCard } from "../components/ChartCard";
import { EChart } from "../components/EChart";
import { EmptyState } from "../components/StateViews";
import { CLUSTER_COLORS, EMOTION_META } from "../config";
import type { DataBundle } from "../types";
import { clusterSummaries, formatPct, pcaProvinceScatter } from "../utils/analytics";
import { clusterInterpretation } from "../utils/metricLabels";
import { dateMonthToShort } from "../utils/dateUtils";
import { cssVar } from "../theme";
import styles from "./Pages.module.css";

interface ClusterAnalysisProps {
  data: DataBundle;
}

const CLUSTER_HEATMAP_COLORS = [
  "#3B7DD8",
  "#5F8FA8",
  "#7D6AAE",
  "#D95C4A",
  "#E7C84F",
  "#A79A8D"
];

export function ClusterAnalysis({ data }: ClusterAnalysisProps) {
  const scatter = useMemo(() => pcaProvinceScatter(data.provinceVectors), [data.provinceVectors]);
  const summaries = useMemo(() => clusterSummaries(data.provinceVectors, data.clusterLabels), [data.clusterLabels, data.provinceVectors]);
  const months = data.monthlyClusters.months;
  const matrixRows = data.monthlyClusters.rows;

  const scatterOption = useMemo<EChartsOption>(() => {
    const clusters = [...new Set(scatter.map((row) => row.cluster))].sort((a, b) => a - b);
    const surfaceColor = cssVar("--surface-solid", "#fff");
    const borderColor = cssVar("--border", "rgba(60,80,110,0.1)");
    const textColor = cssVar("--text", "#1A2332");
    const textSecColor = cssVar("--text-secondary", "#5A6B7E");
    const textMutedColor = cssVar("--text-muted", "#8A98A8");
    return {
      color: [...CLUSTER_COLORS],
      tooltip: {
        backgroundColor: surfaceColor,
        borderColor: borderColor,
        textStyle: { color: textColor },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        formatter: (params: any) => {
          const item = params.data;
          const interp = clusterInterpretation(item[2]);
          return [
            `<strong>${item[3]}</strong>`,
            `${interp.name}`,
            `PC1 ${item[0].toFixed(2)} / PC2 ${item[1].toFixed(2)}`,
            `样本 ${item[4]}`
          ].join("<br/>");
        }
      },
      grid: { left: 44, right: 20, top: 24, bottom: 38 },
      xAxis: {
        name: "PC1",
        nameTextStyle: { color: textMutedColor },
        axisLabel: { color: textMutedColor },
        splitLine: { lineStyle: { color: borderColor } }
      },
      yAxis: {
        name: "PC2",
        nameTextStyle: { color: textMutedColor },
        axisLabel: { color: textMutedColor },
        splitLine: { lineStyle: { color: borderColor } }
      },
      animationDurationUpdate: 600,
      animationEasing: "cubicOut",
      series: clusters.map((cluster) => ({
        name: clusterInterpretation(cluster).name,
        type: "scatter" as const,
        symbolSize: (value: number[]) => Math.max(14, Math.min(36, Math.sqrt(Number(value[4]) || 1) * 5)),
        data: scatter.filter((row) => row.cluster === cluster).map((row) => [row.x, row.y, row.cluster, row.province, row.posts]),
        label: { show: false },
        emphasis: {
          focus: "series" as const,
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          label: { show: true, formatter: (params: any) => params.data[3], color: textColor, fontSize: 12 }
        }
      })),
      legend: {
        top: 0,
        right: 0,
        textStyle: { color: textSecColor }
      }
    };
  }, [scatter]);

  const heatmapOption = useMemo<EChartsOption>(() => {
    const formattedMonths = months.map(dateMonthToShort);
    const validValues = matrixRows.flatMap((row, provinceIndex) =>
      row.values.filter((v) => v >= 0).map((value, monthIndex) => [monthIndex, provinceIndex, value])
    );
    const naValues = matrixRows.flatMap((row, provinceIndex) =>
      row.values.map((value, monthIndex) => (value < 0 ? [monthIndex, provinceIndex, -1] : null)).filter(Boolean)
    );
    const surfaceColor = cssVar("--surface-solid", "#fff");
    const borderColor = cssVar("--border", "rgba(60,80,110,0.1)");
    const textColor = cssVar("--text", "#1A2332");
    const textMutedColor = cssVar("--text-muted", "#8A98A8");
    return {
      tooltip: {
        backgroundColor: surfaceColor,
        borderColor: borderColor,
        textStyle: { color: textColor },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        formatter: (params: any) => {
          const [monthIndex, provinceIndex, value] = params.data;
          const interp = value >= 0 ? clusterInterpretation(value) : null;
          return [
            `<strong>${matrixRows[provinceIndex]?.province}</strong>`,
            formattedMonths[monthIndex as number],
            value >= 0 ? `聚类：${interp?.name ?? `Cluster ${value}`}` : "数据不足"
          ].join("<br/>");
        }
      },
      grid: { left: 70, right: 28, top: 20, bottom: 60 },
      xAxis: {
        type: "category",
        data: formattedMonths,
        axisLabel: { color: textMutedColor, rotate: 35 },
        axisLine: { lineStyle: { color: borderColor } }
      },
      yAxis: {
        type: "category",
        data: matrixRows.map((row) => row.province),
        axisLabel: { color: textMutedColor },
        axisLine: { lineStyle: { color: borderColor } }
      },
      visualMap: {
        min: 0,
        max: Math.max(3, ...validValues.map((v) => v[2] as number)),
        show: false,
        inRange: { color: CLUSTER_HEATMAP_COLORS }
      },
      series: [
        {
          type: "heatmap",
          data: validValues,
          itemStyle: { borderWidth: 1, borderColor: surfaceColor },
          animationDurationUpdate: 600,
          animationEasing: "cubicOut"
        },
        {
          type: "heatmap",
          data: naValues as number[][],
          itemStyle: { borderWidth: 1, borderColor: surfaceColor, color: "rgba(138, 152, 168, 0.15)" },
          silent: true
        }
      ]
    };
  }, [matrixRows, months]);

  return (
    <div className={styles.pageStack}>
      <section className={styles.sectionHeader}>
        <p className={styles.kicker}>CLUSTER ANALYSIS</p>
        <h1>省份情绪聚类</h1>
      </section>
      <div className={styles.clusterGrid}>
        <ChartCard title="省份情绪相似度分布" eyebrow="PCA SCATTER">
          {scatter.length ? <EChart option={scatterOption} height={390} /> : <EmptyState title="暂无聚类数据" />}
        </ChartCard>
        <ChartCard title="月度聚类演进" eyebrow="MONTHLY EVOLUTION">
          {matrixRows.length ? <EChart option={heatmapOption} height={390} /> : <EmptyState title="暂无月度矩阵" />}
        </ChartCard>
      </div>

      <ChartCard title="聚类对照表" eyebrow="CLUSTER PROFILES">
        <div className={styles.tableWrap}>
          <table className={styles.dataTable}>
            <thead>
              <tr>
                <th>聚类</th>
                <th>省份数</th>
                <th>代表省份</th>
                <th>主导情绪</th>
                <th>情绪温度</th>
                <th>样本量</th>
              </tr>
            </thead>
            <tbody>
              {summaries.map((summary) => {
                const interp = clusterInterpretation(summary.cluster);
                return (
                  <tr key={summary.cluster}>
                    <td>
                      <span className={styles.clusterDot} style={{ background: CLUSTER_COLORS[summary.cluster % CLUSTER_COLORS.length] }} />
                      {interp.name}
                    </td>
                    <td>{summary.provinces.length}</td>
                    <td>{summary.provinces.slice(0, 8).join("、")}</td>
                    <td style={{ color: EMOTION_META[summary.dominant].color }}>{EMOTION_META[summary.dominant].label}</td>
                    <td>{formatPct(summary.intensity)}</td>
                    <td>{summary.posts}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </ChartCard>

      <ChartCard title="聚类解读" eyebrow="CLUSTER INTERPRETATION">
        <div className={styles.clusterExplainGrid}>
          {summaries.map((summary) => {
            const interp = clusterInterpretation(summary.cluster);
            return (
              <div key={summary.cluster} className={styles.clusterExplainCard}>
                <h4>
                  <span
                    className={styles.clusterDot}
                    style={{ background: CLUSTER_COLORS[summary.cluster % CLUSTER_COLORS.length] }}
                  />
                  {interp.name}
                </h4>
                <p>{interp.description}</p>
                <p style={{ marginTop: 6, fontSize: 11, color: "var(--text-muted)" }}>
                  代表省份：{summary.provinces.slice(0, 4).join("、")}
                  {summary.provinces.length > 4 ? ` 等${summary.provinces.length}省` : ""}
                </p>
              </div>
            );
          })}
        </div>
      </ChartCard>
    </div>
  );
}
