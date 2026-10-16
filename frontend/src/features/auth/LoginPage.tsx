import { Navigate, useNavigate } from '@tanstack/react-router'
import { useState, type FormEvent } from 'react'

import { ApiError } from '@/shared/api/client'
import { useAuth } from '@/shared/auth/useAuth'
import { Alert } from '@/shared/ui/Alert'
import { Button } from '@/shared/ui/Button'
import { Field } from '@/shared/ui/Field'
import styles from './LoginPage.module.css'

export function LoginPage() {
  const { login: authenticate, status } = useAuth()
  const navigate = useNavigate()
  const [login, setLogin] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await authenticate({ login, password })
      await navigate({ to: '/' })
    } catch (cause) {
      setError(
        cause instanceof ApiError
          ? cause.message
          : 'Something went wrong. Please try again.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  if (status === 'authenticated') {
    return <Navigate to="/" />
  }

  return (
    <div className={styles.page}>
      <div className={styles.panel}>
        <p className="eyebrow">42 · Campus analytics</p>
        <h1 className={styles.title}>Sign in</h1>
        <p className={styles.subtitle}>Track XP, levels, streaks and cohort standing.</p>
        <form className={styles.form} onSubmit={onSubmit}>
          <Field
            label="Login"
            name="login"
            autoComplete="username"
            autoFocus
            required
            value={login}
            onChange={(event) => setLogin(event.target.value)}
          />
          <Field
            label="Password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          {error && <Alert tone="error">{error}</Alert>}
          <Button type="submit" block loading={submitting}>
            {submitting ? 'Signing in' : 'Sign in'}
          </Button>
        </form>
      </div>
      <aside className={styles.side} aria-hidden="true">
        <span className={styles.sideMark}>SPD</span>
        <p className={styles.sideText}>
          Ligne claire interface for student progress at 42.
        </p>
      </aside>
    </div>
  )
}
