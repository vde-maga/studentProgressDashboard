import styles from './Spinner.module.css'

export interface SpinnerProps {
  label?: string
  size?: 'sm' | 'lg'
}

export function Spinner({ label = 'Loading', size = 'sm' }: SpinnerProps) {
  return (
    <span className={[styles.wrap, styles[size]].join(' ')} role="status">
      <span className={styles.dot} aria-hidden="true" />
      <span className="eyebrow">{label}</span>
    </span>
  )
}
