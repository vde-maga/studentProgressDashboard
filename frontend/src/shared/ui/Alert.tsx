import type { ReactNode } from 'react'

import styles from './Alert.module.css'

type Tone = 'error' | 'info' | 'success'

export function Alert({ tone = 'info', children }: { tone?: Tone; children: ReactNode }) {
  return (
    <div className={[styles.alert, styles[tone]].join(' ')} role="alert">
      {children}
    </div>
  )
}
