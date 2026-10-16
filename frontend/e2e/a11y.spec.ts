import { expect, test } from '@playwright/test'

import { STUDENT } from './support/accounts'
import { signIn } from './support/auth'

test('the skip link reveals and focuses the main landmark', async ({ page }) => {
  await signIn(page, STUDENT)

  // The skip link is the first focusable element, so one Tab reaches it.
  await page.keyboard.press('Tab')
  const skipLink = page.getByRole('link', { name: 'Skip to content' })
  await expect(skipLink).toBeFocused()

  await page.keyboard.press('Enter')
  await expect(page.getByRole('main')).toBeFocused()
})

test('client-side navigation moves focus to the new content', async ({ page }) => {
  await signIn(page, STUDENT)

  await page.getByRole('link', { name: 'Leaderboard' }).click()

  await expect(page.getByRole('heading', { name: 'Leaderboard' })).toBeVisible()
  await expect(page.getByRole('main')).toBeFocused()
})
