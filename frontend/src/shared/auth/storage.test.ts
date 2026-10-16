import { beforeEach, describe, expect, it } from 'vitest'

import { clearTokens, readTokens, writeTokens } from './storage'

beforeEach(() => {
  localStorage.clear()
})

describe('token storage', () => {
  it('returns null when nothing is stored', () => {
    expect(readTokens()).toBeNull()
  })

  it('round-trips a token pair', () => {
    writeTokens({ accessToken: 'access', refreshToken: 'refresh' })

    expect(readTokens()).toEqual({ accessToken: 'access', refreshToken: 'refresh' })
  })

  it('clears stored tokens', () => {
    writeTokens({ accessToken: 'access', refreshToken: 'refresh' })

    clearTokens()

    expect(readTokens()).toBeNull()
  })
})
