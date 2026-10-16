import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { AuthStatus } from './context'
import { RequireAuth } from './RequireAuth'

const mocks = vi.hoisted(() => ({ status: 'anonymous' as AuthStatus }))

vi.mock('./useAuth', () => ({
  useAuth: () => ({ status: mocks.status }),
}))

vi.mock('@tanstack/react-router', () => ({
  Navigate: ({ to }: { to: string }) => <div data-testid="redirect">{to}</div>,
}))

describe('RequireAuth', () => {
  it('shows a spinner while the session is loading', () => {
    mocks.status = 'loading'
    render(
      <RequireAuth>
        <p>secret</p>
      </RequireAuth>,
    )

    expect(screen.getByRole('status')).toHaveTextContent('Checking session')
  })

  it('redirects anonymous visitors to the login page', () => {
    mocks.status = 'anonymous'
    render(
      <RequireAuth>
        <p>secret</p>
      </RequireAuth>,
    )

    expect(screen.getByTestId('redirect')).toHaveTextContent('/login')
    expect(screen.queryByText('secret')).not.toBeInTheDocument()
  })

  it('renders its children for an authenticated session', () => {
    mocks.status = 'authenticated'
    render(
      <RequireAuth>
        <p>secret</p>
      </RequireAuth>,
    )

    expect(screen.getByText('secret')).toBeInTheDocument()
  })
})
