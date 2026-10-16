import { expect, test } from '@playwright/test'

import { STUDENT } from './support/accounts'
import { signIn } from './support/auth'
import { emitActivity } from './support/db'

/**
 * Records a short walkthrough used as the README demo GIF. Skipped during a
 * normal run; regenerate on demand with `just demo` (which sets `DEMO=1` and
 * converts the recorded video with ffmpeg). The deterministic seed keeps it
 * reproducible.
 */
test.skip(!process.env.DEMO, 'run `just demo` to regenerate the demo GIF')

test.use({
  viewport: { width: 1280, height: 720 },
  deviceScaleFactor: 1,
  video: { mode: 'on', size: { width: 1280, height: 720 } },
})

test('records a walkthrough of the main flows', async ({ page }) => {
  const pause = (ms: number) => page.waitForTimeout(ms)

  await page.goto('/login')
  await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible()
  await pause(1200)

  await signIn(page, STUDENT)
  await expect(page.getByText('Live', { exact: true })).toBeVisible()
  await expect(page.getByText('Waiting for activity…')).toBeVisible()
  await pause(1400)

  // Give the live stream something to deliver while the page is open.
  emitActivity(STUDENT, 'project_validated')
  await expect(page.getByRole('listitem').filter({ hasText: 'Project' })).toBeVisible()
  await pause(1600)

  await page.getByRole('link', { name: 'Leaderboard' }).click()
  await expect(page.getByRole('heading', { name: 'Leaderboard' })).toBeVisible()
  await pause(1600)

  await page.getByRole('link', { name: 'My profile' }).click()
  await expect(page.getByRole('heading', { name: 'Skills' })).toBeVisible()
  await page.locator('svg').first().waitFor()
  await pause(1800)
})
