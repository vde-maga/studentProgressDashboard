import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { useMemo } from 'react'

import { ActivityFeed, type ActivityRow } from '@/features/activity/ActivityFeed'
import { ApiError } from '@/shared/api/client'
import {
  getStudentActivity,
  getStudentProfile,
  getStudentProgress,
  getStudentSkills,
} from '@/shared/api/endpoints'
import type { ActivityEvent } from '@/shared/api/types'
import { useActivityStream } from '@/shared/api/useActivityStream'
import { useAuth } from '@/shared/auth/useAuth'
import { LineChart } from '@/shared/charts/LineChart'
import { ProgressBar } from '@/shared/charts/ProgressBar'
import { RadarChart } from '@/shared/charts/RadarChart'
import { formatDay, formatLevel, formatXp } from '@/shared/format'
import { Alert } from '@/shared/ui/Alert'
import { Card } from '@/shared/ui/Card'
import { LiveIndicator } from '@/shared/ui/LiveIndicator'
import { Spinner } from '@/shared/ui/Spinner'
import { Stat } from '@/shared/ui/Stat'
import styles from './StudentProfilePage.module.css'

const MAX_LEVEL = 21

function mergeActivity(
  rest: ActivityRow[],
  live: ActivityEvent[],
  limit = 50,
): ActivityRow[] {
  const byId = new Map<number, ActivityRow>()
  for (const row of rest) byId.set(row.id, row)
  for (const event of live) byId.set(event.id, event)
  return [...byId.values()].sort((a, b) => b.id - a.id).slice(0, limit)
}

export interface StudentProfilePageProps {
  login: string
}

export function StudentProfilePage({ login }: StudentProfilePageProps) {
  const { user } = useAuth()

  const profile = useQuery({
    queryKey: ['student', login, 'profile'],
    queryFn: () => getStudentProfile(login),
  })
  const progress = useQuery({
    queryKey: ['student', login, 'progress'],
    queryFn: () => getStudentProgress(login),
    enabled: profile.isSuccess,
  })
  const skills = useQuery({
    queryKey: ['student', login, 'skills'],
    queryFn: () => getStudentSkills(login),
    enabled: profile.isSuccess,
  })
  const activity = useQuery({
    queryKey: ['student', login, 'activity'],
    queryFn: () => getStudentActivity(login, { limit: 50 }),
    enabled: profile.isSuccess,
  })
  const { events, status } = useActivityStream()

  const rows = useMemo(
    () =>
      mergeActivity(
        activity.data ?? [],
        events.filter((event) => event.student_login === login),
      ),
    [activity.data, events, login],
  )

  if (profile.isPending) {
    return <Spinner size="lg" label="Loading profile" />
  }

  if (profile.isError) {
    const error = profile.error
    if (error instanceof ApiError && error.status === 403) {
      return (
        <Alert tone="error">
          You can only view your own profile.{' '}
          {user && (
            <Link to="/students/$login" params={{ login: user.login }}>
              Go to yours
            </Link>
          )}
          .
        </Alert>
      )
    }
    if (error instanceof ApiError && error.status === 404) {
      return <Alert tone="error">No student named “{login}”.</Alert>
    }
    return <Alert tone="error">{error.message}</Alert>
  }

  const data = profile.data
  const levels = (progress.data ?? []).map((point) => Number(point.level))
  const labels = (progress.data ?? []).map((point) => formatDay(point.day))
  const radar = (skills.data ?? []).map((skill) => ({
    label: skill.code,
    value: Number(skill.level),
  }))

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <p className="eyebrow">
            {data.campus.name} · {data.campus.city}
          </p>
          <h1 className={styles.title}>{data.full_name}</h1>
          <p className={styles.login}>@{data.login}</p>
        </div>
        <div className={styles.badges}>
          <span className={styles.rank}>#{data.rank}</span>
          {data.blackholed_at && <span className={styles.blackhole}>Blackholed</span>}
        </div>
      </header>

      <div className={styles.stats}>
        <Stat label="Total XP" value={formatXp(data.xp_total)} />
        <Stat label="Level" value={formatLevel(data.level)} hint="of 21" />
        <Stat label="Projects" value={formatXp(data.projects_done)} />
        <Stat label="Streak" value={`${data.current_streak}d`} hint="consecutive days" />
      </div>

      <Card heading="Level progression" eyebrow="Towards next level">
        <ProgressBar
          value={Number(data.level_progress)}
          label="Progress to next level"
          caption={`${Math.round(Number(data.level_progress) * 100)}% to level ${Math.ceil(Number(data.level))}`}
        />
      </Card>

      <div className={styles.grid}>
        <Card heading="XP over time" eyebrow="Daily snapshots">
          {progress.isPending ? (
            <Spinner label="Loading series" />
          ) : progress.isError ? (
            <Alert tone="error">{progress.error.message}</Alert>
          ) : (
            <LineChart
              values={levels}
              labels={labels}
              ariaLabel={`Level over time for ${data.login}`}
            />
          )}
        </Card>

        <Card heading="Skills" eyebrow="Current levels">
          {skills.isPending ? (
            <Spinner label="Loading skills" />
          ) : skills.isError ? (
            <Alert tone="error">{skills.error.message}</Alert>
          ) : (
            <RadarChart
              data={radar}
              max={MAX_LEVEL}
              ariaLabel={`Skill levels for ${data.login}`}
            />
          )}
        </Card>
      </div>

      <Card
        heading={
          <span className={styles.feedHeading}>
            Activity
            <LiveIndicator status={status} />
          </span>
        }
        eyebrow="Recent events"
      >
        {activity.isPending && rows.length === 0 ? (
          <Spinner label="Loading activity" />
        ) : activity.isError && rows.length === 0 ? (
          <Alert tone="error">{activity.error.message}</Alert>
        ) : (
          <ActivityFeed items={rows} emptyLabel="No activity recorded yet." />
        )}
      </Card>
    </div>
  )
}
