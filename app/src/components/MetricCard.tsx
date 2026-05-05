import { motion } from "framer-motion";
import styles from "./MetricCard.module.css";

const spring = { type: "spring" as const, stiffness: 240, damping: 28, mass: 0.8 };

interface MetricCardProps {
  label: string;
  value: string;
  detail?: string;
  tone?: "warm" | "cool" | "danger" | "neutral";
}

export function MetricCard({ label, value, detail, tone = "neutral" }: MetricCardProps) {
  return (
    <motion.article
      className={`${styles.card} ${styles[tone]}`}
      whileHover={{ scale: 1.02, y: -2 }}
      transition={spring}
    >
      <span className={styles.label}>{label}</span>
      <strong>{value}</strong>
      {detail ? <small>{detail}</small> : null}
    </motion.article>
  );
}
