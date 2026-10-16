import styles from './ProgressBar.module.css'

export interface ProgressBarProps {
  /** Fraction between 0 and 1. */
  value: number
  label?: string
  caption?: string
}

export function ProgressBar({ value, label, caption }: ProgressBarProps) {
  const ratio = Math.min(Math.max(value, 0), 1)
  const percent = Math.round(ratio * 100)
  return (
    <div className={styles.wrap}>
      <div
        className={styles.track}
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label ?? 'Progress'}
      >
        <div className={styles.fill} style={{ width: `${percent}%` }} />
      </div>
      {caption && <span className={`eyebrow ${styles.caption}`}>{caption}</span>}
    </div>
  )
}
