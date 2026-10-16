import { useSyncExternalStore } from 'react'

import { dismiss, getSnapshot, subscribe } from './store'
import styles from './Toaster.module.css'

/**
 * Bottom-corner stack of transient error notices fed by the query caches.
 * Announcements use a polite live region so screen readers pick them up.
 */
export function Toaster() {
  const notifications = useSyncExternalStore(subscribe, getSnapshot)
  if (notifications.length === 0) return null
  return (
    <div className={styles.region} role="status" aria-live="polite">
      {notifications.map((notification) => (
        <div key={notification.id} className={styles.toast}>
          <span className={styles.message}>{notification.message}</span>
          <button
            type="button"
            className={styles.close}
            onClick={() => dismiss(notification.id)}
            aria-label="Dismiss notification"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  )
}
