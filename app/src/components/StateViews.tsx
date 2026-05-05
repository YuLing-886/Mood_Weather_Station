import styles from "./StateViews.module.css";

export function Skeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className={styles.skeleton} aria-busy="true">
      {Array.from({ length: rows }, (_, index) => (
        <span key={index} style={{ width: `${92 - index * 13}%` }} />
      ))}
    </div>
  );
}

export function EmptyState({ title, detail }: { title: string; detail?: string }) {
  return (
    <div className={styles.empty}>
      <strong>{title}</strong>
      {detail ? <p>{detail}</p> : null}
    </div>
  );
}
