import { screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import * as endpoints from '@/shared/api/endpoints'
import { ApiError } from '@/shared/api/client'
import type { StudentProfile } from '@/shared/api/types'
import { renderWithProviders } from '@/test/render'
import { StudentProfilePage } from './StudentProfilePage'

vi.mock('@/shared/api/useActivityStream', () => ({
  useActivityStream: () => ({ events: [], status: 'open' }),
}))

vi.mock('@/shared/api/endpoints', () => ({
  getStudentProfile: vi.fn(),
  getStudentProgress: vi.fn(),
  getStudentSkills: vi.fn(),
  getStudentActivity: vi.fn(),
}))

const profile: StudentProfile = {
  id: 1,
  login: 'ada',
  full_name: 'Ada Lovelace',
  role: 'student',
  campus: {
    id: 1,
    code: 'LON',
    name: 'London',
    city: 'London',
    country: 'United Kingdom',
  },
  xp_total: 45000,
  level: '21.00',
  level_progress: '0.00',
  projects_done: 42,
  rank: 3,
  current_streak: 12,
  blackholed_at: null,
  created_at: '2024-01-01T00:00:00Z',
}

function mockAll() {
  vi.mocked(endpoints.getStudentProfile).mockResolvedValue(profile)
  vi.mocked(endpoints.getStudentProgress).mockResolvedValue([
    { day: '2026-03-10', xp_total: 40000, level: '20.00', projects_done: 40 },
    { day: '2026-03-12', xp_total: 45000, level: '21.00', projects_done: 42 },
  ])
  vi.mocked(endpoints.getStudentSkills).mockResolvedValue([
    { code: 'algo', name: 'Algorithms', level: '15.00' },
    { code: 'unix', name: 'Unix', level: '10.00' },
    { code: 'graphics', name: 'Graphics', level: '8.00' },
  ])
  vi.mocked(endpoints.getStudentActivity).mockResolvedValue([
    {
      id: 7,
      kind: 'commit',
      day: '2026-03-12',
      xp_delta: 100,
      project_slug: 'push_swap',
      occurred_at: '2026-03-12T09:00:00Z',
    },
  ])
}

describe('StudentProfilePage', () => {
  it('renders the profile, stats and activity', async () => {
    mockAll()

    renderWithProviders(<StudentProfilePage login="ada" />)

    expect(await screen.findByText('Ada Lovelace')).toBeInTheDocument()
    expect(screen.getByText('@ada')).toBeInTheDocument()
    expect(screen.getByText('45,000')).toBeInTheDocument()
    expect(screen.getByText('#3')).toBeInTheDocument()
    expect(await screen.findByText('push_swap')).toBeInTheDocument()
  })

  it('shows a not-found message for an unknown student', async () => {
    vi.mocked(endpoints.getStudentProfile).mockRejectedValue(
      new ApiError(404, 'student_not_found', 'No such student.'),
    )

    renderWithProviders(<StudentProfilePage login="ada" />)

    expect(await screen.findByRole('alert')).toHaveTextContent('No student named')
  })
})
