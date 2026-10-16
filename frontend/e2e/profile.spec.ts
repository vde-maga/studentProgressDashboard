import { expect, test } from '@playwright/test'

import { OTHER_STUDENT, STUDENT } from './support/accounts'
import { signIn } from './support/auth'

test('opens a student profile from the leaderboard', async ({ page }) => {
  await signIn(page, STUDENT)

  await page.getByRole('link', { name: 'Leaderboard' }).click()
  await expect(page.getByRole('heading', { name: 'Leaderboard' })).toBeVisible()

  // A student can only open their own profile, so follow their own row instead.
  await page.getByRole('link', { name: new RegExp(STUDENT) }).click()

  await expect(page).toHaveURL(new RegExp(`/students/${STUDENT}$`))
  await expect(page.getByText('Total XP')).toBeVisible()
  await expect(page.locator('svg').first()).toBeVisible()
})

test('lets the student view their own profile', async ({ page }) => {
  await signIn(page, STUDENT)

  await page.getByRole('link', { name: 'My profile' }).click()

  await expect(page).toHaveURL(new RegExp(`/students/${STUDENT}$`))
  await expect(page.getByText(`@${STUDENT}`)).toBeVisible()
  await expect(page.getByText('Total XP')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Skills' })).toBeVisible()
  await expect(page.locator('svg').first()).toBeVisible()
})

test('refuses to show another student’s profile', async ({ page }) => {
  await signIn(page, STUDENT)

  await page.goto(`/students/${OTHER_STUDENT}`)

  await expect(page.getByRole('alert')).toContainText(
    'You can only view your own profile',
  )
})
