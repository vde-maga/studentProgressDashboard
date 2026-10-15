import { useQuery } from '@tanstack/react-query'

import { getCohortSummary } from '@/shared/api/endpoints'
import { useAuth } from '@/shared/auth/useAuth'
import { formatLevel, formatXp } from '@/shared/format'
import { Alert } from '@/shared/ui/Alert'
import { Spinner } from '@/shared/ui/Spinner'
import { Stat } from '@/shared/ui/Stat'
import styles from './DashboardPage.module.css'

export function DashboardPage() {
  const { user } = useAuth()
  const { data, isPending, isError, error } = useQuery({
    queryKey: ['cohort', 'summary'],
    queryFn: getCohortSummary,
  })

  return (
    <div className={styles.page}>
      <header className={styles.intro}>
        <p className="eyebrow">Cohort overview</p>
        <h1 className={styles.title}>Welcome back{user ? `, ${user.full_name}` : ''}</h1>
        <p className={styles.lead}>
          Aggregate progress across every student in the cohort.
        </p>
      </header>

      {isPending && <Spinner size="lg" label="Loading cohort" />}
      {isError && <Alert tone="error">{error.message}</Alert>}

      {data && (
        <div className={styles.grid}>
          <Stat label="Students" value={formatXp(data.student_count)} />
          <Stat label="Total XP" value={formatXp(data.total_xp)} />
          <Stat
            label="Average level"
            value={formatLevel(data.average_level)}
            hint="of 21"
          />
          <Stat label="Projects done" value={formatXp(data.projects_done)} />
          <Stat label="Active (7 days)" value={formatXp(data.active_last_7_days)} />
        </div>
      )}
    </div>
  )
}
