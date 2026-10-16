import type { ActivityKind } from '@/shared/api/types'
import { formatDay, formatXp } from '@/shared/format'
import styles from './ActivityFeed.module.css'

const KIND_LABEL: Record<ActivityKind, string> = {
  login: 'Login',
  commit: 'Commit',
  evaluation_given: 'Eval given',
  evaluation_received: 'Eval received',
  project_validated: 'Project',
}

export interface ActivityRow {
  id: number
  kind: ActivityKind
  day: string
  xp_delta: number
  project_slug: string | null
  student_login?: string
}

export interface ActivityFeedProps {
  items: ActivityRow[]
  showStudent?: boolean
  emptyLabel?: string
}

export function ActivityFeed({
  items,
  showStudent = false,
  emptyLabel = 'No activity yet.',
}: ActivityFeedProps) {
  if (items.length === 0) {
    return <p className={styles.empty}>{emptyLabel}</p>
  }
  return (
    <ol className={styles.feed} aria-live="polite" aria-relevant="additions">
      {items.map((item) => (
        <li key={item.id} className={styles.row}>
          <span className={styles.kind}>{KIND_LABEL[item.kind]}</span>
          <span className={styles.detail}>
            {showStudent && item.student_login && (
              <strong className={styles.student}>{item.student_login}</strong>
            )}
            <span className={styles.project}>{item.project_slug ?? '—'}</span>
          </span>
          <span className={`numeric ${styles.day}`}>{formatDay(item.day)}</span>
          <span
            className={`numeric ${styles.xp} ${item.xp_delta >= 0 ? styles.up : styles.down}`}
          >
            {item.xp_delta >= 0 ? '+' : '−'}
            {formatXp(Math.abs(item.xp_delta))}
          </span>
        </li>
      ))}
    </ol>
  )
}
