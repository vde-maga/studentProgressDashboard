/** Runtime configuration, resolved from Vite env vars at build time. */

const rawBase = (import.meta.env.VITE_API_URL ?? '').trim()

/** Origin of the API, or `''` to use same-origin (Vite dev proxy). */
export const API_BASE_URL = rawBase.replace(/\/$/, '')

/** Versioned API prefix, e.g. `'' + '/api/v1'` in development. */
export const API_PREFIX = `${API_BASE_URL}/api/v1`
