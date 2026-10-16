import type { StreamStatus } from '@/shared/api/useActivityStream'

import styles from './LiveIndicator.module.css'

export interface LiveIndicatorProps {
  status: StreamStatus
}

/**
 * Connection state of the live activity stream. A live region announces the
 * change from "Connecting" to "Live" so it is not conveyed by colour alone.
 */
export function LiveIndicator({ status }: LiveIndicatorProps) {
  const live = status === 'open'
  return (
    <span
      className={[styles.indicator, live ? styles.on : ''].filter(Boolean).join(' ')}
      role="status"
    >
      <span aria-hidden="true">●</span>
      <span>{live ? 'Live' : 'Connecting'}</span>
    </span>
  )
}
