import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/shared/api/client'
import { LoginPage } from './LoginPage'

const mocks = vi.hoisted(() => ({
  login: vi.fn(),
  navigate: vi.fn(),
  auth: { status: 'anonymous' as 'anonymous' | 'authenticated' },
}))

vi.mock('@/shared/auth/useAuth', () => ({
  useAuth: () => ({ status: mocks.auth.status, login: mocks.login }),
}))

vi.mock('@tanstack/react-router', () => ({
  Navigate: () => null,
  useNavigate: () => mocks.navigate,
}))

beforeEach(() => {
  vi.clearAllMocks()
  mocks.auth.status = 'anonymous'
})

describe('LoginPage', () => {
  it('authenticates with the entered credentials and navigates home', async () => {
    mocks.login.mockResolvedValue(undefined)
    render(<LoginPage />)

    await userEvent.type(screen.getByLabelText('Login'), 'ada')
    await userEvent.type(screen.getByLabelText('Password'), 'secret')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    await waitFor(() =>
      expect(mocks.login).toHaveBeenCalledWith({ login: 'ada', password: 'secret' }),
    )
    expect(mocks.navigate).toHaveBeenCalledWith({ to: '/' })
  })

  it('surfaces the API error message on failure', async () => {
    mocks.login.mockRejectedValue(
      new ApiError(401, 'invalid_credentials', 'Invalid login or password.'),
    )
    render(<LoginPage />)

    await userEvent.type(screen.getByLabelText('Login'), 'ada')
    await userEvent.type(screen.getByLabelText('Password'), 'wrong')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Invalid login or password.',
    )
    expect(mocks.navigate).not.toHaveBeenCalled()
  })

  it('falls back to a generic message for unexpected errors', async () => {
    mocks.login.mockRejectedValue(new Error('boom'))
    render(<LoginPage />)

    await userEvent.type(screen.getByLabelText('Login'), 'ada')
    await userEvent.type(screen.getByLabelText('Password'), 'secret')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Something went wrong. Please try again.',
    )
  })

  it('redirects away when already authenticated', () => {
    mocks.auth.status = 'authenticated'
    render(<LoginPage />)

    expect(screen.queryByLabelText('Login')).not.toBeInTheDocument()
  })
})
