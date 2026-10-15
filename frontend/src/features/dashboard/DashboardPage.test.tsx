import { screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import * as endpoints from '@/shared/api/endpoints'
import type { CohortSummary } from '@/shared/api/types'
import { renderWithProviders } from '@/test/render'
import { DashboardPage } from './DashboardPage'

vi.mock('@/shared/api/endpoints', () => ({
  getCohortSummary: vi.fn(),
}))

vi.mock('@/shared/api/useActivityStream', () => ({
  useActivityStream: () => ({ events: [], status: 'connecting' }),
}))

const summary: CohortSummary = {
  student_count: 120,
  total_xp: 45000,
  average_level: '9.63',
  projects_done: 340,
  active_last_7_days: 42,
}

describe('DashboardPage', () => {
  it('renders the cohort aggregate figures', async () => {
    vi.mocked(endpoints.getCohortSummary).mockResolvedValue(summary)

    renderWithProviders(<DashboardPage />)

    expect(await screen.findByText('45,000')).toBeInTheDocument()
    expect(screen.getByText('9.63')).toBeInTheDocument()
    expect(screen.getByText('120')).toBeInTheDocument()
  })

  it('shows an error message when the request fails', async () => {
    vi.mocked(endpoints.getCohortSummary).mockRejectedValue(new Error('boom'))

    renderWithProviders(<DashboardPage />)

    expect(await screen.findByRole('alert')).toHaveTextContent('boom')
  })
})
