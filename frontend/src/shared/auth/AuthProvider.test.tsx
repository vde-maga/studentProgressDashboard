import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as endpoints from '@/shared/api/endpoints'
import type { UserProfile } from '@/shared/api/types'
import { AuthProvider } from './AuthProvider'
import { readTokens, writeTokens } from './storage'
import { useAuth } from './useAuth'

vi.mock('@/shared/api/endpoints', () => ({
  getCurrentUser: vi.fn(),
  login: vi.fn(),
}))

const profile: UserProfile = {
  id: 1,
  login: 'ada',
  email: 'ada@example.com',
  full_name: 'Ada Lovelace',
  role: 'student',
  campus_id: 1,
  blackholed_at: null,
  created_at: '2024-01-01T00:00:00Z',
}

function Probe() {
  const { status, user, login, logout } = useAuth()
  return (
    <div>
      <span data-testid="status">{status}</span>
      <span data-testid="user">{user?.login ?? 'none'}</span>
      <button onClick={() => void login({ login: 'ada', password: 'x' })}>
        do-login
      </button>
      <button onClick={logout}>logout</button>
    </div>
  )
}

function renderProvider() {
  render(
    <AuthProvider>
      <Probe />
    </AuthProvider>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
})

describe('AuthProvider', () => {
  it('starts anonymous when no tokens are stored', () => {
    renderProvider()

    expect(screen.getByTestId('status')).toHaveTextContent('anonymous')
    expect(screen.getByTestId('user')).toHaveTextContent('none')
  })

  it('restores the session from stored tokens', async () => {
    writeTokens({ accessToken: 'a', refreshToken: 'r' })
    vi.mocked(endpoints.getCurrentUser).mockResolvedValue(profile)

    renderProvider()

    await waitFor(() =>
      expect(screen.getByTestId('status')).toHaveTextContent('authenticated'),
    )
    expect(screen.getByTestId('user')).toHaveTextContent('ada')
  })

  it('clears tokens when the stored session can no longer be restored', async () => {
    writeTokens({ accessToken: 'a', refreshToken: 'r' })
    vi.mocked(endpoints.getCurrentUser).mockRejectedValue(new Error('expired'))

    renderProvider()

    await waitFor(() =>
      expect(screen.getByTestId('status')).toHaveTextContent('anonymous'),
    )
    expect(readTokens()).toBeNull()
  })

  it('stores tokens and loads the profile on login', async () => {
    vi.mocked(endpoints.login).mockResolvedValue({
      access_token: 'new-access',
      refresh_token: 'new-refresh',
      token_type: 'bearer',
      expires_in: 900,
    })
    vi.mocked(endpoints.getCurrentUser).mockResolvedValue(profile)
    renderProvider()

    await userEvent.click(screen.getByRole('button', { name: 'do-login' }))

    await waitFor(() =>
      expect(screen.getByTestId('status')).toHaveTextContent('authenticated'),
    )
    expect(readTokens()).toEqual({
      accessToken: 'new-access',
      refreshToken: 'new-refresh',
    })
  })

  it('clears the session on logout', async () => {
    writeTokens({ accessToken: 'a', refreshToken: 'r' })
    vi.mocked(endpoints.getCurrentUser).mockResolvedValue(profile)
    renderProvider()
    await waitFor(() =>
      expect(screen.getByTestId('status')).toHaveTextContent('authenticated'),
    )

    await userEvent.click(screen.getByRole('button', { name: 'logout' }))

    expect(screen.getByTestId('status')).toHaveTextContent('anonymous')
    expect(readTokens()).toBeNull()
  })
})
