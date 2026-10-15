import {
  createRootRoute,
  createRoute,
  createRouter,
  Outlet,
} from '@tanstack/react-router'

import { AppShell } from '@/app/AppShell'
import { LoginPage } from '@/features/auth/LoginPage'
import { DashboardPage } from '@/features/dashboard/DashboardPage'
import { LeaderboardPage } from '@/features/leaderboard/LeaderboardPage'
import { NotFoundPage } from '@/features/notfound/NotFoundPage'
import { RequireAuth } from '@/shared/auth/RequireAuth'

const rootRoute = createRootRoute({
  component: () => <Outlet />,
  notFoundComponent: NotFoundPage,
})

// Pathless layout route: everything under it renders inside the app chrome.
const appRoute = createRoute({
  getParentRoute: () => rootRoute,
  id: 'app',
  component: AppShell,
})

const dashboardRoute = createRoute({
  getParentRoute: () => appRoute,
  path: '/',
  component: () => (
    <RequireAuth>
      <DashboardPage />
    </RequireAuth>
  ),
})

const leaderboardRoute = createRoute({
  getParentRoute: () => appRoute,
  path: '/leaderboard',
  component: () => (
    <RequireAuth>
      <LeaderboardPage />
    </RequireAuth>
  ),
})

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: LoginPage,
})

const routeTree = rootRoute.addChildren([
  appRoute.addChildren([dashboardRoute, leaderboardRoute]),
  loginRoute,
])

export const router = createRouter({
  routeTree,
  defaultPreload: 'intent',
})

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
