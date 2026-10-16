import { resolve } from 'node:path'

import { expect, test } from '@playwright/test'

import { STUDENT } from './support/accounts'
import { signIn } from './support/auth'

/**
 * README screenshots. Skipped during a normal run; regenerate on demand with
 * `just screenshots` (which sets `SCREENSHOTS=1`). The deterministic seed keeps
 * them reproducible.
 */
test.skip(!process.env.SCREENSHOTS, 'run `just screenshots` to regenerate')

const OUT = resolve(process.cwd(), '..', 'docs', 'screenshots')

test.use({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 })

test('captures the main screens', async ({ page }) => {
  await page.goto('/login')
  await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible()
  await page.screenshot({ path: `${OUT}/01-login.png` })

  await signIn(page, STUDENT)
  await page.getByText('Live', { exact: true }).waitFor()
  await page.screenshot({ path: `${OUT}/02-dashboard.png`, fullPage: true })

  await page.getByRole('link', { name: 'Leaderboard' }).click()
  await expect(page.getByRole('heading', { name: 'Leaderboard' })).toBeVisible()
  await page.screenshot({ path: `${OUT}/03-leaderboard.png`, fullPage: true })

  await page.getByRole('link', { name: 'My profile' }).click()
  await expect(page.getByRole('heading', { name: 'Skills' })).toBeVisible()
  await page.locator('svg').first().waitFor()
  await page.screenshot({ path: `${OUT}/04-profile.png`, fullPage: true })
})
