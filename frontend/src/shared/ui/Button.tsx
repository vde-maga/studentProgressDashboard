import type { ButtonHTMLAttributes } from 'react'

import styles from './Button.module.css'

type Variant = 'primary' | 'secondary' | 'ghost'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  loading?: boolean
  block?: boolean
}

export function Button({
  variant = 'primary',
  loading = false,
  block = false,
  disabled,
  className,
  children,
  type = 'button',
  ...rest
}: ButtonProps) {
  const classes = [styles.button, styles[variant]]
  if (block) classes.push(styles.block)
  if (className) classes.push(className)
  return (
    <button
      type={type}
      className={classes.filter(Boolean).join(' ')}
      disabled={disabled ?? loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {children}
    </button>
  )
}
