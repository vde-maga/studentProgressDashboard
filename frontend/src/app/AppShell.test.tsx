import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  RouterProvider,
} from '@tanstack/react-router'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '@/shared/auth/AuthProvider'
import { clearTokens } from '@/shared/auth/storage'
import { AppShell } from './AppShell'

function renderShell() {
  const rootRoute = createRootRoute({ component: AppShell })
  const indexRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/',
    component: () => <p>dashboard content</p>,
  })
  const boardRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/leaderboard',
    component: () => <p>leaderboard content</p>,
  })
  const router = createRouter({
    routeTree: rootRoute.addChildren([indexRoute, boardRoute]),
    history: createMemoryHistory({ initialEntries: ['/'] }),
  })
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </QueryClientProvider>,
  )
  return router
}

beforeEach(() => {
  clearTokens()
  vi.stubGlobal('scrollTo', vi.fn())
})

describe('AppShell', () => {
  it('offers a skip link targeting the main landmark', async () => {
    renderShell()

    const skipLink = await screen.findByRole('link', { name: /skip to content/i })
    expect(skipLink).toHaveAttribute('href', '#main')
    expect(screen.getByRole('main')).toHaveAttribute('id', 'main')
  })

  it('moves focus to the main landmark on navigation', async () => {
    const user = userEvent.setup()
    renderShell()

    const leaderboard = await screen.findByRole('link', { name: 'Leaderboard' })
    await user.click(leaderboard)

    expect(await screen.findByText('leaderboard content')).toBeInTheDocument()
    expect(screen.getByRole('main')).toHaveFocus()
  })
})
