/**
 * API contract types.
 *
 * These mirror the Pydantic response models on the backend. Note that every
 * `Decimal` field arrives as a JSON *string* (Pydantic renders Decimals as
 * strings to preserve precision), hence `level: string` rather than `number`.
 */

export type Role = 'student' | 'staff' | 'admin'

export type ActivityKind =
  'login' | 'commit' | 'evaluation_given' | 'evaluation_received' | 'project_validated'

export interface LoginRequest {
  login: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

/** The authenticated user as returned by `GET /auth/me`. */
export interface UserProfile {
  id: number
  login: string
  email: string
  full_name: string
  role: Role
  campus_id: number
  blackholed_at: string | null
  created_at: string
}

export interface Campus {
  id: number
  code: string
  name: string
  city: string
  country: string
}

export interface StudentSummary {
  id: number
  login: string
  full_name: string
  role: Role
  campus_id: number
  blackholed_at: string | null
  created_at: string
}

export interface StudentListResponse {
  items: StudentSummary[]
  total: number
  limit: number
  offset: number
}

export interface StudentProfile {
  id: number
  login: string
  full_name: string
  role: Role
  campus: Campus
  xp_total: number
  level: string
  level_progress: string
  projects_done: number
  rank: number
  current_streak: number
  blackholed_at: string | null
  created_at: string
}

export interface ProgressPoint {
  day: string
  xp_total: number
  level: string
  projects_done: number
}

export interface ActivityItem {
  id: number
  kind: ActivityKind
  day: string
  xp_delta: number
  project_slug: string | null
  occurred_at: string
}

export interface SkillLevel {
  code: string
  name: string
  level: string
}

export interface LeaderboardEntry {
  rank: number
  login: string
  full_name: string
  campus_code: string
  xp_total: number
  level: string
  projects_done: number
}

export interface CohortSummary {
  student_count: number
  total_xp: number
  average_level: string
  projects_done: number
  active_last_7_days: number
}

/** A single `data:` frame of the activity SSE stream. */
export interface ActivityEvent {
  id: number
  kind: ActivityKind
  student_login: string
  day: string
  xp_delta: number
  project_slug: string | null
  occurred_at: string
}
