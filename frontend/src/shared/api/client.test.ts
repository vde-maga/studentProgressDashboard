import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  clearTokens,
  readTokens,
  UNAUTHORIZED_EVENT,
  writeTokens,
} from '@/shared/auth/storage'
import { ApiError, apiRequest } from './client'

const fetchMock = vi.fn()

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function problem(code: string, detail: string, status: number): Response {
  return new Response(JSON.stringify({ code, detail }), {
    status,
    headers: { 'Content-Type': 'application/problem+json' },
  })
}

function authorizationOfCall(index: number): string | null {
  const call = fetchMock.mock.calls[index]
  const init = call?.[1] as RequestInit | undefined
  return new Headers(init?.headers).get('Authorization')
}

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock)
  fetchMock.mockReset()
  clearTokens()
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('apiRequest', () => {
  it('attaches the bearer token', async () => {
    writeTokens({ accessToken: 'access-1', refreshToken: 'refresh-1' })
    fetchMock.mockResolvedValueOnce(json({ ok: true }))

    const result = await apiRequest<{ ok: boolean }>('/thing')

    expect(result).toEqual({ ok: true })
    expect(authorizationOfCall(0)).toBe('Bearer access-1')
  })

  it('refreshes once and retries after a 401', async () => {
    writeTokens({ accessToken: 'stale', refreshToken: 'refresh-1' })
    fetchMock
      .mockResolvedValueOnce(problem('unauthorized', 'expired', 401))
      .mockResolvedValueOnce(
        json({
          access_token: 'fresh',
          refresh_token: 'refresh-2',
          token_type: 'bearer',
          expires_in: 900,
        }),
      )
      .mockResolvedValueOnce(json({ ok: true }))

    const result = await apiRequest<{ ok: boolean }>('/thing')

    expect(result).toEqual({ ok: true })
    expect(readTokens()).toEqual({
      accessToken: 'fresh',
      refreshToken: 'refresh-2',
    })
    expect(authorizationOfCall(2)).toBe('Bearer fresh')
  })

  it('clears the session and emits an event when refresh fails', async () => {
    writeTokens({ accessToken: 'stale', refreshToken: 'refresh-1' })
    const listener = vi.fn()
    window.addEventListener(UNAUTHORIZED_EVENT, listener)
    fetchMock
      .mockResolvedValueOnce(problem('unauthorized', 'expired', 401))
      .mockResolvedValueOnce(problem('unauthorized', 'bad refresh', 401))

    await expect(apiRequest('/thing')).rejects.toBeInstanceOf(ApiError)

    expect(readTokens()).toBeNull()
    expect(listener).toHaveBeenCalledTimes(1)
    window.removeEventListener(UNAUTHORIZED_EVENT, listener)
  })

  it('surfaces the problem code and detail on failure', async () => {
    fetchMock.mockResolvedValueOnce(
      problem('invalid_credentials', 'Invalid login or password.', 401),
    )

    await expect(apiRequest('/auth/login', { auth: false })).rejects.toMatchObject({
      status: 401,
      code: 'invalid_credentials',
      message: 'Invalid login or password.',
    })
  })
})
