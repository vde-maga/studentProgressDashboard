import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Field } from './Field'

describe('Field', () => {
  it('ties the label to the input and exposes a hint', () => {
    render(<Field label="Login" name="login" hint="Your 42 username" />)

    const input = screen.getByLabelText('Login')
    expect(input).toHaveAccessibleDescription('Your 42 username')
  })

  it('marks the input invalid and announces the error instead of the hint', () => {
    render(<Field label="Login" name="login" hint="Your 42 username" error="Required" />)

    const input = screen.getByLabelText('Login')
    expect(input).toHaveAttribute('aria-invalid', 'true')
    expect(screen.getByRole('alert')).toHaveTextContent('Required')
    expect(screen.queryByText('Your 42 username')).not.toBeInTheDocument()
  })
})
