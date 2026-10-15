import type { HTMLAttributes, ReactNode } from 'react'

import styles from './Card.module.css'

export interface CardProps extends HTMLAttributes<HTMLElement> {
  heading?: ReactNode
  eyebrow?: ReactNode
  as?: 'section' | 'article' | 'div'
}

export function Card({
  heading,
  eyebrow,
  as: Tag = 'section',
  className,
  children,
  ...rest
}: CardProps) {
  const classes = [styles.card, className].filter(Boolean).join(' ')
  return (
    <Tag className={classes} {...rest}>
      {(heading || eyebrow) && (
        <header className={styles.header}>
          {eyebrow && <span className="eyebrow">{eyebrow}</span>}
          {heading && <h2 className={styles.title}>{heading}</h2>}
        </header>
      )}
      {children}
    </Tag>
  )
}
