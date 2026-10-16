import { expect, test } from '@playwright/test'

import { STUDENT } from './support/accounts'
import { signIn } from './support/auth'
import { emitActivity } from './support/db'

test('shows the cohort summary', async ({ page }) => {
  await signIn(page, STUDENT)

  await expect(page.getByText('Cohort overview')).toBeVisible()
  for (const label of ['Students', 'Total XP', 'Average level', 'Projects done']) {
    await expect(page.getByText(label, { exact: true })).toBeVisible()
  }
})

test('delivers a new activity event over the live stream', async ({ page }) => {
  await signIn(page, STUDENT)

  // The stream has connected (and captured its cursor) once the marker reads live.
  await expect(page.getByTitle('Live')).toBeVisible()
  await expect(page.getByText('Waiting for activity…')).toBeVisible()

  emitActivity(STUDENT, 'project_validated')

  await expect(page.getByRole('listitem').filter({ hasText: 'Project' })).toBeVisible()
})
