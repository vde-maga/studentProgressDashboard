import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import { getCurrentUser, login as loginRequest } from '@/shared/api/endpoints'
import type { LoginRequest, UserProfile } from '@/shared/api/types'
import { AuthContext, type AuthStatus } from './context'
import { clearTokens, readTokens, UNAUTHORIZED_EVENT, writeTokens } from './storage'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [status, setStatus] = useState<AuthStatus>(() =>
    readTokens() ? 'loading' : 'anonymous',
  )

  useEffect(() => {
    if (!readTokens()) return
    let active = true
    getCurrentUser()
      .then((profile) => {
        if (!active) return
        setUser(profile)
        setStatus('authenticated')
      })
      .catch(() => {
        if (!active) return
        clearTokens()
        setStatus('anonymous')
      })
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    const onUnauthorized = () => {
      setUser(null)
      setStatus('anonymous')
    }
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized)
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized)
  }, [])

  const login = useCallback(async (credentials: LoginRequest) => {
    const tokens = await loginRequest(credentials)
    writeTokens({
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
    })
    const profile = await getCurrentUser()
    setUser(profile)
    setStatus('authenticated')
  }, [])

  const logout = useCallback(() => {
    clearTokens()
    setUser(null)
    setStatus('anonymous')
  }, [])

  const value = useMemo(
    () => ({ status, user, login, logout }),
    [status, user, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
