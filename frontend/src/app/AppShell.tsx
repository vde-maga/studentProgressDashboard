import { Link, Outlet, useRouterState } from '@tanstack/react-router'
import { useEffect, useRef } from 'react'

import { useAuth } from '@/shared/auth/useAuth'
import { Button } from '@/shared/ui/Button'
import styles from './AppShell.module.css'

export function AppShell() {
  const { user, logout } = useAuth()
  const pathname = useRouterState({ select: (state) => state.location.pathname })
  const mainRef = useRef<HTMLElement>(null)
  const isFirstRender = useRef(true)

  // Move focus to the main landmark on navigation so keyboard and screen-reader
  // users land on the new content instead of staying on the activated link.
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false
      return
    }
    mainRef.current?.focus()
  }, [pathname])

  return (
    <div className={styles.shell}>
      <a href="#main" className={styles.skipLink}>
        Skip to content
      </a>
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
      <main id="main" ref={mainRef} tabIndex={-1} className={styles.main}>
        <Outlet />
      </main>
    </div>
  )
}
