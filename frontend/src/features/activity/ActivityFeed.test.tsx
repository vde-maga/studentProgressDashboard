import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { ActivityFeed } from './ActivityFeed'

describe('ActivityFeed', () => {
  it('exposes the list as a polite live region', () => {
    render(
      <ActivityFeed
        items={[
          {
            id: 1,
            kind: 'commit',
            day: '2026-03-12',
            xp_delta: 100,
            project_slug: 'push_swap',
          },
        ]}
      />,
    )

    const list = screen.getByRole('list')
    expect(list).toHaveAttribute('aria-live', 'polite')
    expect(list).toHaveAttribute('aria-relevant', 'additions')
  })

  it('renders the empty label when there are no events', () => {
    render(<ActivityFeed items={[]} emptyLabel="Nothing here yet." />)
    expect(screen.getByText('Nothing here yet.')).toBeInTheDocument()
  })
})
