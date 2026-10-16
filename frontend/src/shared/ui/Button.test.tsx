import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { Button } from './Button'

describe('Button', () => {
  it('renders its children and defaults to a non-submit button', () => {
    render(<Button>Save</Button>)

    const button = screen.getByRole('button', { name: 'Save' })
    expect(button).toHaveAttribute('type', 'button')
    expect(button).toBeEnabled()
  })

  it('disables itself and reports busy while loading', () => {
    render(<Button loading>Saving</Button>)

    const button = screen.getByRole('button', { name: 'Saving' })
    expect(button).toBeDisabled()
    expect(button).toHaveAttribute('aria-busy', 'true')
  })

  it('forwards clicks when enabled', () => {
    const onClick = vi.fn()
    render(<Button onClick={onClick}>Go</Button>)

    screen.getByRole('button', { name: 'Go' }).click()

    expect(onClick).toHaveBeenCalledOnce()
  })
})
