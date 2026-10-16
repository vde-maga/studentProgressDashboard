import { screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { ReactNode } from 'react'

import * as endpoints from '@/shared/api/endpoints'
import { ApiError } from '@/shared/api/client'
import type { LeaderboardEntry } from '@/shared/api/types'
import { renderWithProviders } from '@/test/render'
import { LeaderboardPage } from './LeaderboardPage'

vi.mock('@/shared/api/endpoints', () => ({
  getLeaderboard: vi.fn(),
  getCurrentUser: vi.fn(),
}))

vi.mock('@tanstack/react-router', () => ({
  Link: ({ children }: { children: ReactNode }) => <span>{children}</span>,
}))

const entries: LeaderboardEntry[] = [
  {
    rank: 1,
    login: 'ada',
    full_name: 'Ada Lovelace',
    campus_code: 'LON',
    xp_total: 45000,
    level: '21.00',
    projects_done: 42,
  },
]

describe('LeaderboardPage', () => {
  it('renders the ranking with formatted values', async () => {
    vi.mocked(endpoints.getLeaderboard).mockResolvedValue(entries)

    renderWithProviders(<LeaderboardPage />)

    expect(await screen.findByText('Ada Lovelace')).toBeInTheDocument()
    expect(screen.getByText('45,000')).toBeInTheDocument()
    expect(screen.getByText('Top 1 students')).toBeInTheDocument()
  })

  it('shows a spinner while the ranking loads', () => {
    vi.mocked(endpoints.getLeaderboard).mockReturnValue(new Promise(() => {}))

    renderWithProviders(<LeaderboardPage />)

    expect(screen.getByRole('status')).toHaveTextContent('Loading ranking')
  })

  it('surfaces an error when the ranking fails', async () => {
    vi.mocked(endpoints.getLeaderboard).mockRejectedValue(
      new ApiError(500, 'internal_error', 'The ranking is unavailable.'),
    )

    renderWithProviders(<LeaderboardPage />)

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'The ranking is unavailable.',
    )
  })
})
