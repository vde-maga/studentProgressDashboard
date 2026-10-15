import { useId } from 'react'

import { scaleSeries, toAreaPath, toLinePath } from './geometry'
import styles from './LineChart.module.css'

const WIDTH = 640
const HEIGHT = 220
const PADDING = 16

export interface LineChartProps {
  values: number[]
  labels?: string[]
  ariaLabel: string
}

export function LineChart({ values, labels, ariaLabel }: LineChartProps) {
  const gradientId = `spark-${useId().replace(/:/g, '')}`

  if (values.length === 0) {
    return <p className={styles.empty}>No data yet.</p>
  }

  const points = scaleSeries(values, WIDTH, HEIGHT, PADDING)
  const last = points[points.length - 1]
  const baseline = HEIGHT - PADDING

  return (
    <figure className={styles.figure}>
      <svg
        className={styles.svg}
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        preserveAspectRatio="none"
        role="img"
        aria-label={ariaLabel}
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--color-secondary)" stopOpacity="0.35" />
            <stop offset="100%" stopColor="var(--color-secondary)" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path
          className={styles.area}
          d={toAreaPath(points, baseline)}
          fill={`url(#${gradientId})`}
        />
        <path className={styles.line} d={toLinePath(points)} />
        {last && <circle className={styles.marker} cx={last.x} cy={last.y} r={5} />}
      </svg>
      {labels && labels.length > 0 && (
        <figcaption className={`eyebrow ${styles.caption}`}>
          <span>{labels[0]}</span>
          <span>{labels[labels.length - 1]}</span>
        </figcaption>
      )}
    </figure>
  )
}
