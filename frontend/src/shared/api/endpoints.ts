/** Typed wrappers around every API endpoint the UI uses. */

import { API_PREFIX } from '@/shared/config'
import { readTokens } from '@/shared/auth/storage'
import { apiRequest } from './client'
import type {
  ActivityItem,
  CohortSummary,
  LeaderboardEntry,
  LoginRequest,
  ProgressPoint,
  SkillLevel,
  StudentListResponse,
  StudentProfile,
  TokenResponse,
  UserProfile,
} from './types'

function query(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) search.set(key, String(value))
  }
  const encoded = search.toString()
  return encoded ? `?${encoded}` : ''
}

export function login(credentials: LoginRequest): Promise<TokenResponse> {
  return apiRequest<TokenResponse>('/auth/login', {
    method: 'POST',
    body: credentials,
    auth: false,
  })
}

export function getCurrentUser(): Promise<UserProfile> {
  return apiRequest<UserProfile>('/auth/me')
}

export function getCohortSummary(): Promise<CohortSummary> {
  return apiRequest<CohortSummary>('/cohort/summary')
}

export function getLeaderboard(
  params: { limit?: number; offset?: number } = {},
): Promise<LeaderboardEntry[]> {
  return apiRequest<LeaderboardEntry[]>(`/leaderboard${query(params)}`)
}

export function listStudents(
  params: { limit?: number; offset?: number } = {},
): Promise<StudentListResponse> {
  return apiRequest<StudentListResponse>(`/students${query(params)}`)
}

export function getStudentProfile(login: string): Promise<StudentProfile> {
  return apiRequest<StudentProfile>(`/students/${encodeURIComponent(login)}`)
}

export function getStudentProgress(
  login: string,
  params: { since?: string; until?: string } = {},
): Promise<ProgressPoint[]> {
  return apiRequest<ProgressPoint[]>(
    `/students/${encodeURIComponent(login)}/progress${query(params)}`,
  )
}

export function getStudentActivity(
  login: string,
  params: { limit?: number } = {},
): Promise<ActivityItem[]> {
  return apiRequest<ActivityItem[]>(
    `/students/${encodeURIComponent(login)}/activity${query(params)}`,
  )
}

export function getStudentSkills(login: string): Promise<SkillLevel[]> {
  return apiRequest<SkillLevel[]>(`/students/${encodeURIComponent(login)}/skills`)
}

/**
 * Build the SSE URL for the live activity stream. `EventSource` cannot send
 * custom headers, so the access token travels in the `token` query parameter.
 */
export function streamEventsUrl(): string {
  const tokens = readTokens()
  const token = tokens ? query({ token: tokens.accessToken }) : ''
  return `${API_PREFIX}/events/stream${token}`
}
