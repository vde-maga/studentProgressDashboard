import { Link } from '@tanstack/react-router'

import styles from './NotFoundPage.module.css'

export function NotFoundPage() {
  return (
    <div className={styles.page}>
      <p className="eyebrow">Error 404</p>
      <h1 className={styles.title}>Page not found</h1>
      <p className={styles.lead}>
        That route does not exist. <Link to="/">Return to the dashboard</Link>.
      </p>
    </div>
  )
}
