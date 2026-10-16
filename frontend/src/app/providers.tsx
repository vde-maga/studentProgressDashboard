import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query'
import { useState, type ReactNode } from 'react'

import { shouldRetry } from '@/shared/api/retry'
import { AuthProvider } from '@/shared/auth/AuthProvider'
import { Toaster } from '@/shared/notifications/Toaster'
import { notify } from '@/shared/notifications/store'

function messageOf(error: unknown): string {
  if (error instanceof Error && error.message) return error.message
  return 'Something went wrong.'
}

/** Compose the app-wide providers (data fetching + authentication). */
export function AppProviders({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        queryCache: new QueryCache({
          // A query that already had data and failed while refetching has no
          // contextual UI, so surface it. Initial-load errors render inline.
          onError: (error, query) => {
            if (query.state.data !== undefined) notify(messageOf(error))
          },
        }),
        mutationCache: new MutationCache({
          onError: (error) => notify(messageOf(error)),
        }),
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            retry: shouldRetry,
            refetchOnWindowFocus: false,
          },
        },
      }),
  )
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
      <Toaster />
    </QueryClientProvider>
  )
}
