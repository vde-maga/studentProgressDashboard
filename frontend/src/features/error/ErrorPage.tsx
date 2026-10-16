import { Button } from '@/shared/ui/Button'
import styles from './ErrorPage.module.css'

export interface ErrorPageProps {
  error?: unknown
  /** Retry handler; when omitted (e.g. hard render failure) only reload is offered. */
  onRetry?: () => void
}

function messageOf(error: unknown): string {
  if (error instanceof Error && error.message) return error.message
  if (typeof error === 'string' && error) return error
  return 'The page failed to render.'
}

/**
 * Full-page fallback shown when a route or the component tree throws. Uses a
 * plain anchor (not the router `Link`) so it still works when the router itself
 * is the thing that failed to render.
 */
export function ErrorPage({ error, onRetry }: ErrorPageProps) {
  return (
    <div className={styles.page} role="alert">
      <p className="eyebrow">Unexpected error</p>
      <h1 className={styles.title}>Something broke</h1>
      <p className={styles.lead}>{messageOf(error)}</p>
      <div className={styles.actions}>
        {onRetry && (
          <Button variant="primary" onClick={onRetry}>
            Try again
          </Button>
        )}
        <a className={styles.link} href="/">
          Back to dashboard
        </a>
      </div>
    </div>
  )
}
