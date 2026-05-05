import type { ReactNode } from "react";
import { motion } from "framer-motion";
import styles from "./ChartCard.module.css";

const spring = { type: "spring" as const, stiffness: 240, damping: 28, mass: 0.8 };

interface ChartCardProps {
  title: string;
  eyebrow?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function ChartCard({ title, eyebrow, action, children, className = "" }: ChartCardProps) {
  return (
    <motion.section
      className={`${styles.card} ${className}`}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={spring}
    >
      <header className={styles.header}>
        <div>
          {eyebrow ? <p className={styles.eyebrow}>{eyebrow}</p> : null}
          <h2>{title}</h2>
        </div>
        {action ? <div className={styles.action}>{action}</div> : null}
      </header>
      <div className={styles.body}>{children}</div>
    </motion.section>
  );
}
