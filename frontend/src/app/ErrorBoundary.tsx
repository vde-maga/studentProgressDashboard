import { Component, type ErrorInfo, type ReactNode } from 'react'

import { ErrorPage } from '@/features/error/ErrorPage'

interface ErrorBoundaryProps {
  children: ReactNode
}

interface ErrorBoundaryState {
  error: Error | null
}

/**
 * Last line of defence around the whole app. Catches render/lifecycle errors
 * that escape the router's own boundary and shows `ErrorPage` instead of an
 * empty document.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  override state: ErrorBoundaryState = { error: null }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error }
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('Unhandled application error', error, info.componentStack)
  }

  private readonly reset = () => this.setState({ error: null })

  override render(): ReactNode {
    if (this.state.error) {
      return <ErrorPage error={this.state.error} onRetry={this.reset} />
    }
    return this.props.children
  }
}
