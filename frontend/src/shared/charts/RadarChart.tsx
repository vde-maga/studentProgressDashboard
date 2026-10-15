import { radarSpokes, ringPolygon, toPointsAttribute } from './geometry'
import styles from './RadarChart.module.css'

const SIZE = 340
const CENTER = SIZE / 2
const RADIUS = SIZE / 2 - 52
const RINGS = [0.25, 0.5, 0.75, 1]

export interface RadarDatum {
  label: string
  value: number
}

export interface RadarChartProps {
  data: RadarDatum[]
  max: number
  ariaLabel: string
}

function anchorFor(x: number): 'start' | 'middle' | 'end' {
  if (x < CENTER - 12) return 'end'
  if (x > CENTER + 12) return 'start'
  return 'middle'
}

export function RadarChart({ data, max, ariaLabel }: RadarChartProps) {
  if (data.length < 3) {
    return <p className={styles.empty}>Not enough skills to plot.</p>
  }

  const spokes = radarSpokes(
    data.map((datum) => datum.value),
    max,
    CENTER,
    RADIUS,
  )
  const labelPoints = radarSpokes(
    data.map(() => 1),
    1,
    CENTER,
    RADIUS + 18,
  )
  const axes = ringPolygon(data.length, CENTER, RADIUS)

  return (
    <figure className={styles.figure}>
      <svg
        className={styles.svg}
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        role="img"
        aria-label={ariaLabel}
      >
        {RINGS.map((ratio) => (
          <polygon
            key={ratio}
            className={styles.ring}
            points={toPointsAttribute(ringPolygon(data.length, CENTER, RADIUS * ratio))}
          />
        ))}
        {axes.map((point) => (
          <line
            key={`${point.x}-${point.y}`}
            className={styles.axis}
            x1={CENTER}
            y1={CENTER}
            x2={point.x}
            y2={point.y}
          />
        ))}
        <polygon className={styles.shape} points={toPointsAttribute(spokes)} />
        {data.map((datum, index) => {
          const point = labelPoints[index]
          if (!point) return null
          return (
            <text
              key={datum.label}
              className={styles.label}
              x={point.x}
              y={point.y}
              textAnchor={anchorFor(point.x)}
              dominantBaseline="middle"
            >
              {datum.label}
            </text>
          )
        })}
      </svg>
    </figure>
  )
}
