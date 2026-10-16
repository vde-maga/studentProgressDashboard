import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { LiveIndicator } from './LiveIndicator'

describe('LiveIndicator', () => {
  it('announces the connecting state', () => {
    render(<LiveIndicator status="connecting" />)
    expect(screen.getByRole('status')).toHaveTextContent('Connecting')
  })

  it('announces the live state', () => {
    render(<LiveIndicator status="open" />)
    expect(screen.getByRole('status')).toHaveTextContent('Live')
  })
})
