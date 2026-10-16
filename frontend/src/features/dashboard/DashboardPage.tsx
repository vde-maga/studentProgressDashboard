import { useQuery } from '@tanstack/react-query'

import { ActivityFeed } from '@/features/activity/ActivityFeed'
import { getCohortSummary } from '@/shared/api/endpoints'
import { useActivityStream } from '@/shared/api/useActivityStream'
import { useAuth } from '@/shared/auth/useAuth'
import { formatLevel, formatXp } from '@/shared/format'
import { Alert } from '@/shared/ui/Alert'
import { Card } from '@/shared/ui/Card'
import { LiveIndicator } from '@/shared/ui/LiveIndicator'
import { Spinner } from '@/shared/ui/Spinner'
import { Stat } from '@/shared/ui/Stat'
import styles from './DashboardPage.module.css'

export function DashboardPage() {
  const { user } = useAuth()
  const summary = useQuery({
    queryKey: ['cohort', 'summary'],
    queryFn: getCohortSummary,
  })
  const { events, status } = useActivityStream(15)

  return (
    <div className={styles.page}>
      <header className={styles.intro}>
        <p className="eyebrow">Cohort overview</p>
        <h1 className={styles.title}>Welcome back{user ? `, ${user.full_name}` : ''}</h1>
        <p className={styles.lead}>
          Aggregate progress across every student in the cohort.
        </p>
      </header>

      {summary.isPending && <Spinner size="lg" label="Loading cohort" />}
      {summary.isError && <Alert tone="error">{summary.error.message}</Alert>}

      {summary.data && (
        <div className={styles.grid}>
          <Stat label="Students" value={formatXp(summary.data.student_count)} />
          <Stat label="Total XP" value={formatXp(summary.data.total_xp)} />
          <Stat
            label="Average level"
            value={formatLevel(summary.data.average_level)}
            hint="of 21"
          />
          <Stat label="Projects done" value={formatXp(summary.data.projects_done)} />
          <Stat
            label="Active (7 days)"
            value={formatXp(summary.data.active_last_7_days)}
          />
        </div>
      )}

      <Card
        heading={
          <span className={styles.feedHeading}>
            Live activity
            <LiveIndicator status={status} />
          </span>
        }
        eyebrow="Across the cohort"
      >
        <ActivityFeed items={events} showStudent emptyLabel="Waiting for activity…" />
      </Card>
    </div>
  )
}
