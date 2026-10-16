import { beforeEach, describe, expect, it, vi } from 'vitest'

import { apiRequest } from './client'
import {
  getCohortSummary,
  getCurrentUser,
  getLeaderboard,
  getStudentActivity,
  getStudentProfile,
  getStudentProgress,
  getStudentSkills,
  listStudents,
  login,
} from './endpoints'

vi.mock('./client', () => ({ apiRequest: vi.fn() }))

const request = vi.mocked(apiRequest)

beforeEach(() => {
  vi.clearAllMocks()
  request.mockResolvedValue(undefined)
})

describe('endpoints', () => {
  it('posts credentials without auth for login', async () => {
    await login({ login: 'ada', password: 'secret' })

    expect(request).toHaveBeenCalledWith('/auth/login', {
      method: 'POST',
      body: { login: 'ada', password: 'secret' },
      auth: false,
    })
  })

  it('requests the current user, cohort summary and student list', async () => {
    await getCurrentUser()
    await getCohortSummary()
    await listStudents({ limit: 10 })

    expect(request).toHaveBeenCalledWith('/auth/me')
    expect(request).toHaveBeenCalledWith('/cohort/summary')
    expect(request).toHaveBeenCalledWith('/students?limit=10')
  })

  it('serialises defined query params and skips undefined ones', async () => {
    await getLeaderboard({ limit: 50, offset: undefined })

    expect(request).toHaveBeenCalledWith('/leaderboard?limit=50')
  })

  it('omits the query string entirely when there are no params', async () => {
    await getLeaderboard()

    expect(request).toHaveBeenCalledWith('/leaderboard')
  })

  it('url-encodes the login path segment', async () => {
    await getStudentProfile('a b')
    await getStudentProgress('a b', { since: '2026-01-01' })
    await getStudentSkills('a b')
    await getStudentActivity('a b', { limit: 5 })

    expect(request).toHaveBeenCalledWith('/students/a%20b')
    expect(request).toHaveBeenCalledWith('/students/a%20b/progress?since=2026-01-01')
    expect(request).toHaveBeenCalledWith('/students/a%20b/skills')
    expect(request).toHaveBeenCalledWith('/students/a%20b/activity?limit=5')
  })
})
