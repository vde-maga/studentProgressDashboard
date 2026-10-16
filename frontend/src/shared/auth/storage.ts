/**
 * Persistence of the bearer token pair.
 *
 * Tokens live in `localStorage`, which is shared across tabs and survives
 * reloads. This is a deliberate trade-off for a client-side SPA: it keeps the
 * session usable without a backend session store, at the cost of XSS exposure,
 * mitigated by the app having no untrusted HTML injection points.
 */

const ACCESS_KEY = 'spd.access_token'
const REFRESH_KEY = 'spd.refresh_token'

export interface Tokens {
  accessToken: string
  refreshToken: string
}

function storage(): Storage | null {
  try {
    return typeof window === 'undefined' ? null : window.localStorage
  } catch {
    return null
  }
}

export function readTokens(): Tokens | null {
  const store = storage()
  if (!store) return null
  const accessToken = store.getItem(ACCESS_KEY)
  const refreshToken = store.getItem(REFRESH_KEY)
  if (!accessToken || !refreshToken) return null
  return { accessToken, refreshToken }
}

export function writeTokens(tokens: Tokens): void {
  const store = storage()
  if (!store) return
  store.setItem(ACCESS_KEY, tokens.accessToken)
  store.setItem(REFRESH_KEY, tokens.refreshToken)
}

export function clearTokens(): void {
  const store = storage()
  if (!store) return
  store.removeItem(ACCESS_KEY)
  store.removeItem(REFRESH_KEY)
}

/** Event dispatched when the session is gone and the user must log in again. */
export const UNAUTHORIZED_EVENT = 'spd:unauthorized'
