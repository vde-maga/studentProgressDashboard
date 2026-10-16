import { ApiError } from './client'

/**
 * Retry policy for React Query: transient failures only. Client errors (4xx)
 * are deterministic, so retrying just delays the inevitable — and the 401
 * refresh/redirect flow lives inside the API client, not in the retry loop.
 */
export function shouldRetry(failureCount: number, error: unknown): boolean {
  if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
    return false
  }
  return failureCount < 1
}
