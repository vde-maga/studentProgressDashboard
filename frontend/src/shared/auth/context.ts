import { createContext } from 'react'

import type { LoginRequest, UserProfile } from '@/shared/api/types'

export type AuthStatus = 'loading' | 'authenticated' | 'anonymous'

export interface AuthContextValue {
  status: AuthStatus
  user: UserProfile | null
  login: (credentials: LoginRequest) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)
