import { expect, type Page } from '@playwright/test'

import { DEMO_PASSWORD } from './accounts'

/** Sign in through the real form and wait for the dashboard. */
export async function signIn(
  page: Page,
  login: string,
  password: string = DEMO_PASSWORD,
): Promise<void> {
  await page.goto('/login')
  await page.getByLabel('Login').fill(login)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page.getByRole('heading', { level: 1 })).toContainText('Welcome back')
}
