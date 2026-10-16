import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'

import { getLeaderboard } from '@/shared/api/endpoints'
import { formatLevel, formatXp } from '@/shared/format'
import { Alert } from '@/shared/ui/Alert'
import { Card } from '@/shared/ui/Card'
import { Spinner } from '@/shared/ui/Spinner'
import styles from './LeaderboardPage.module.css'

export function LeaderboardPage() {
  const { data, isPending, isError, error } = useQuery({
    queryKey: ['leaderboard'],
    queryFn: () => getLeaderboard({ limit: 50 }),
  })

  return (
    <div className={styles.page}>
      <header className={styles.intro}>
        <p className="eyebrow">Ranking</p>
        <h1 className={styles.title}>Leaderboard</h1>
        <p className={styles.lead}>The cohort ranked by total XP.</p>
      </header>

      {isPending && <Spinner size="lg" label="Loading ranking" />}
      {isError && <Alert tone="error">{error.message}</Alert>}

      {data && (
        <Card className={styles.card}>
          <div className={styles.scroll}>
            <table className={styles.table}>
              <caption className="eyebrow">Top {data.length} students</caption>
              <thead>
                <tr>
                  <th scope="col">#</th>
                  <th scope="col">Student</th>
                  <th scope="col">Campus</th>
                  <th scope="col" className={styles.num}>
                    XP
                  </th>
                  <th scope="col" className={styles.num}>
                    Level
                  </th>
                  <th scope="col" className={styles.num}>
                    Projects
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.map((entry) => (
                  <tr key={entry.login}>
                    <td className={`numeric ${styles.rank}`}>{entry.rank}</td>
                    <td>
                      <Link
                        to="/students/$login"
                        params={{ login: entry.login }}
                        className={styles.studentLink}
                      >
                        <span className={styles.login}>{entry.login}</span>
                        <span className={styles.name}>{entry.full_name}</span>
                      </Link>
                    </td>
                    <td className="numeric">{entry.campus_code}</td>
                    <td className={`numeric ${styles.num}`}>
                      {formatXp(entry.xp_total)}
                    </td>
                    <td className={`numeric ${styles.num}`}>
                      {formatLevel(entry.level)}
                    </td>
                    <td className={`numeric ${styles.num}`}>
                      {formatXp(entry.projects_done)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}
