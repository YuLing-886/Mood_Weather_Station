import { useMemo, useState, type CSSProperties } from "react";
import { ChartCard } from "../components/ChartCard";
import { EmptyState } from "../components/StateViews";
import { EMOTION_META, EMOTIONS, SEVERITY_ORDER, type EmotionKey } from "../config";
import type { AnomalyEvent, DataBundle } from "../types";
import { severityLabel, zScoreDescription, deviationDescription } from "../utils/metricLabels";
import { dateWeekToShortRange, dateWeekToFullRange } from "../utils/dateUtils";
import { MethodDrawer } from "../components/MethodDrawer";
import styles from "./Pages.module.css";

interface EventTimelineProps {
  data: DataBundle;
}

type EmotionFilter = EmotionKey | "all";
type SeverityFilter = "all" | "moderate" | "severe" | "extreme";

const severities: SeverityFilter[] = ["all", "moderate", "severe", "extreme"];

function friendlyEventDescription(event: AnomalyEvent): string {
  const emotionLabel = EMOTION_META[event.emotion]?.label ?? event.emotion;
  const deviation = deviationDescription(event.deviation_pct);
  return `${dateWeekToShortRange(event.date_week)}，${emotionLabel}情绪出现${severityLabel(event.severity)}，${deviation}。`;
}

export function EventTimeline({ data }: EventTimelineProps) {
  const [emotion, setEmotion] = useState<EmotionFilter>("all");
  const [severity, setSeverity] = useState<SeverityFilter>("all");

  const events = useMemo(() => {
    return [...data.anomalies]
      .filter((event) => emotion === "all" || event.emotion === emotion)
      .filter((event) => severity === "all" || event.severity === severity)
      .sort((a, b) => {
        const weekDelta = a.date_week.localeCompare(b.date_week);
        if (weekDelta) return weekDelta;
        return (SEVERITY_ORDER[b.severity] ?? 0) - (SEVERITY_ORDER[a.severity] ?? 0);
      });
  }, [data.anomalies, emotion, severity]);

  return (
    <div className={styles.pageStack}>
      <section className={styles.sectionHeader}>
        <p className={styles.kicker}>EVENT TIMELINE</p>
        <h1>情绪异常时间线</h1>
        <MethodDrawer trigger="指标说明" />
      </section>

      <ChartCard
        title="异常筛选"
        eyebrow="FILTERS"
        action={<span className={styles.countBadge}>{events.length} 个事件</span>}
      >
        <div className={styles.filterRows}>
          <div className={styles.segmented}>
            <button className={emotion === "all" ? styles.activePill : ""} onClick={() => setEmotion("all")}>全部</button>
            {EMOTIONS.map((key) => (
              <button key={key} className={emotion === key ? styles.activePill : ""} onClick={() => setEmotion(key)}>
                {EMOTION_META[key].label}
              </button>
            ))}
          </div>
          <div className={styles.segmented}>
            {severities.map((item) => (
              <button key={item} className={severity === item ? styles.activePill : ""} onClick={() => setSeverity(item)}>
                {item === "all" ? "全部" : severityLabel(item)}
              </button>
            ))}
          </div>
        </div>
      </ChartCard>

      <ChartCard title="异常节点" eyebrow="EMOTION ANOMALIES">
        {events.length ? (
          <div className={styles.timeline}>
            {events.map((event) => (
              <EventNode event={event} key={`${event.date_week}-${event.emotion}-${event.z_score}`} />
            ))}
          </div>
        ) : (
          <EmptyState title="暂无匹配事件" detail="当前筛选条件下没有异常节点" />
        )}
      </ChartCard>
    </div>
  );
}

function EventNode({ event }: { event: AnomalyEvent }) {
  const color = EMOTION_META[event.emotion].color;
  const provinces = event.top_provinces.map((item) => String(item.province)).filter(Boolean);
  return (
    <article className={styles.timelineItem} style={{ "--event-color": color } as CSSProperties}>
      <div className={styles.timelineStem} />
      <div className={styles.timelineContent}>
        <div className={styles.timelineTopline}>
          <span>{dateWeekToFullRange(event.date_week)}</span>
          <strong>{EMOTION_META[event.emotion].label}</strong>
          <em>{severityLabel(event.severity)}</em>
        </div>
        <p>{friendlyEventDescription(event)}</p>
        <dl className={styles.eventStats}>
          <div>
            <dt>异常强度</dt>
            <dd>{zScoreDescription(event.z_score)}</dd>
          </div>
          <div>
            <dt>全国值</dt>
            <dd>{(event.national_value * 100).toFixed(1)}%</dd>
          </div>
          <div>
            <dt>变化趋势</dt>
            <dd>{deviationDescription(event.deviation_pct)}</dd>
          </div>
        </dl>
        <div className={styles.provinceChips}>
          {provinces.slice(0, 6).map((province) => (
            <span key={province}>{province}</span>
          ))}
        </div>
      </div>
    </article>
  );
}
