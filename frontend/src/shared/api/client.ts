/**
 * Thin typed fetch client for the SPD API.
 *
 * Responsibilities: attach the bearer token, surface RFC 7807 problem
 * responses as `ApiError`, and transparently refresh an expired access token
 * once per failed request (single-flight, so concurrent 401s share a refresh).
 */

import { API_PREFIX } from '@/shared/config'
import {
  clearTokens,
  readTokens,
  UNAUTHORIZED_EVENT,
  writeTokens,
} from '@/shared/auth/storage'
import type { TokenResponse } from './types'

/** An error carrying the HTTP status and RFC 7807 `code` from the API. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

interface ProblemBody {
  code?: string
  detail?: string
  title?: string
}

export interface RequestOptions {
  method?: string
  body?: unknown
  /** Attach the bearer token and allow a refresh retry. Defaults to `true`. */
  auth?: boolean
  signal?: AbortSignal
}

function send(path: string, options: RequestOptions): Promise<Response> {
  const { method = 'GET', body, auth = true, signal } = options
  const headers = new Headers({ Accept: 'application/json' })
  if (body !== undefined) headers.set('Content-Type', 'application/json')
  if (auth) {
    const tokens = readTokens()
    if (tokens) headers.set('Authorization', `Bearer ${tokens.accessToken}`)
  }
  return fetch(`${API_PREFIX}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    signal,
  })
}

async function toError(response: Response): Promise<ApiError> {
  let code = 'http_error'
  let message = response.statusText || `HTTP ${response.status}`
  try {
    const body = (await response.json()) as ProblemBody
    code = body.code ?? code
    message = body.detail ?? body.title ?? message
  } catch {
    // Non-JSON error body; keep the status-derived message.
  }
  return new ApiError(response.status, code, message)
}

async function parse<T>(response: Response): Promise<T> {
  if (response.status === 204) return undefined as T
  const text = await response.text()
  return (text ? JSON.parse(text) : undefined) as T
}

let refreshInFlight: Promise<boolean> | null = null

function ensureRefreshed(): Promise<boolean> {
  refreshInFlight ??= performRefresh().finally(() => {
    refreshInFlight = null
  })
  return refreshInFlight
}

async function performRefresh(): Promise<boolean> {
  const tokens = readTokens()
  if (!tokens) return false
  try {
    const response = await fetch(`${API_PREFIX}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: tokens.refreshToken }),
    })
    if (!response.ok) return false
    const data = (await response.json()) as TokenResponse
    writeTokens({
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
    })
    return true
  } catch {
    return false
  }
}

/** Perform an HTTP request against the API, returning the parsed JSON body. */
export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const auth = options.auth ?? true
  let response = await send(path, options)

  if (response.status === 401 && auth) {
    if (await ensureRefreshed()) {
      response = await send(path, options)
    } else {
      clearTokens()
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new Event(UNAUTHORIZED_EVENT))
      }
    }
  }

  if (!response.ok) throw await toError(response)
  return parse<T>(response)
}
