import type { ReactNode } from 'react'

import styles from './Stat.module.css'

export interface StatProps {
  label: ReactNode
  value: ReactNode
  hint?: ReactNode
}

export function Stat({ label, value, hint }: StatProps) {
  return (
    <article className={styles.stat}>
      <span className="eyebrow">{label}</span>
      <span className={styles.value}>{value}</span>
      {hint && <span className={styles.hint}>{hint}</span>}
    </article>
  )
}
