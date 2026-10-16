import { Navigate } from '@tanstack/react-router'
import type { ReactNode } from 'react'

import { Spinner } from '@/shared/ui/Spinner'
import { useAuth } from './useAuth'

/** Gate a route on an authenticated session, redirecting to `/login` otherwise. */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  if (status === 'loading') {
    return (
      <div style={{ padding: 'var(--space-6)' }}>
        <Spinner size="lg" label="Checking session" />
      </div>
    )
  }
  if (status === 'anonymous') {
    return <Navigate to="/login" />
  }
  return <>{children}</>
}
