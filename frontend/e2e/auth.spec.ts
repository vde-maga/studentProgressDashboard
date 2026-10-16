import { expect, test } from '@playwright/test'

import { STUDENT } from './support/accounts'
import { signIn } from './support/auth'

test('redirects anonymous visitors to the sign-in page', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveURL(/\/login$/)
  await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible()
})

test('rejects bad credentials', async ({ page }) => {
  await page.goto('/login')
  await page.getByLabel('Login').fill(STUDENT)
  await page.getByLabel('Password').fill('not-the-password')
  await page.getByRole('button', { name: 'Sign in' }).click()

  await expect(page.getByRole('alert')).toBeVisible()
  await expect(page).toHaveURL(/\/login$/)
})

test('signs a student in and back out', async ({ page }) => {
  await signIn(page, STUDENT)
  await expect(page.getByText(`${STUDENT} · student`)).toBeVisible()

  await page.getByRole('button', { name: 'Log out' }).click()
  await expect(page).toHaveURL(/\/login$/)
})
