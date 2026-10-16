import { describe, expect, it } from 'vitest'

import { ApiError } from './client'
import { shouldRetry } from './retry'

describe('shouldRetry', () => {
  it('does not retry deterministic client errors', () => {
    expect(shouldRetry(0, new ApiError(404, 'not_found', 'nope'))).toBe(false)
    expect(shouldRetry(0, new ApiError(403, 'forbidden', 'nope'))).toBe(false)
    expect(shouldRetry(0, new ApiError(401, 'unauthorized', 'nope'))).toBe(false)
  })

  it('retries transient server errors exactly once', () => {
    const serverError = new ApiError(503, 'unavailable', 'later')
    expect(shouldRetry(0, serverError)).toBe(true)
    expect(shouldRetry(1, serverError)).toBe(false)
  })

  it('retries unknown (network) errors once', () => {
    const networkError = new Error('Failed to fetch')
    expect(shouldRetry(0, networkError)).toBe(true)
    expect(shouldRetry(1, networkError)).toBe(false)
  })
})
