import { Link, Outlet } from '@tanstack/react-router'

import { useAuth } from '@/shared/auth/useAuth'
import { Button } from '@/shared/ui/Button'
import styles from './AppShell.module.css'

export function AppShell() {
  const { user, logout } = useAuth()
  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <Link to="/" className={styles.brand}>
          <span className={styles.mark}>SPD</span>
          <span className={styles.brandText}>Student Progress Dashboard</span>
        </Link>
        <nav className={styles.nav} aria-label="Primary">
          <Link
            to="/"
            className={styles.link}
            activeProps={{ className: styles.active }}
            activeOptions={{ exact: true }}
          >
            Dashboard
          </Link>
          <Link to="/leaderboard" className={styles.link}>
            Leaderboard
          </Link>
          {user && (
            <Link
              to="/students/$login"
              params={{ login: user.login }}
              className={styles.link}
            >
              My profile
            </Link>
          )}
        </nav>
        <div className={styles.user}>
          {user && (
            <span className="eyebrow">
              {user.login} · {user.role}
            </span>
          )}
          <Button variant="ghost" onClick={logout}>
            Log out
          </Button>
        </div>
      </header>
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  )
}
