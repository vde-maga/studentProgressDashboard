import { defineConfig, devices } from '@playwright/test'

/**
 * End-to-end tests run the real stack: the seeded API and the Vite dev server
 * (which proxies `/api` to it). The database is *not* managed here — start it
 * first (`just db-up`, or a PostgreSQL service in CI); `just e2e-api` applies
 * migrations and seeds it before the API starts.
 */

const FRONTEND_URL = process.env.E2E_BASE_URL ?? 'http://localhost:5173'
const API_URL = process.env.E2E_API_URL ?? 'http://localhost:8000'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: process.env.CI ? [['github'], ['list']] : 'list',
  timeout: 30_000,
  expect: { timeout: 10_000 },

  use: {
    baseURL: FRONTEND_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'off',
  },

  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],

  webServer: [
    {
      command: 'just e2e-api',
      cwd: '..',
      url: `${API_URL}/api/v1/health`,
      timeout: 180_000,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'pnpm dev --port 5173 --strictPort',
      url: FRONTEND_URL,
      timeout: 60_000,
      reuseExistingServer: !process.env.CI,
    },
  ],
})
