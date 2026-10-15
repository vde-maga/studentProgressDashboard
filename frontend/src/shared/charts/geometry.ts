/**
 * Pure geometry helpers for the SVG charts.
 *
 * Kept free of React so the maths is unit-tested directly: scaling a series
 * into a box, turning points into path strings, and laying out radar spokes.
 */

export interface Point {
  x: number
  y: number
}

function bounds(values: number[]): { min: number; max: number } {
  const min = Math.min(...values, 0)
  const max = Math.max(...values, 1)
  return { min, max: max === min ? min + 1 : max }
}

/**
 * Scale a series of values into a `width x height` box (top-left origin),
 * with the smallest value resting on the bottom edge.
 */
export function scaleSeries(
  values: number[],
  width: number,
  height: number,
  padding = 0,
): Point[] {
  if (values.length === 0) return []
  const { min, max } = bounds(values)
  const span = max - min
  const innerWidth = width - padding * 2
  const innerHeight = height - padding * 2
  const toY = (value: number) =>
    padding + innerHeight - ((value - min) / span) * innerHeight
  if (values.length === 1) {
    return [{ x: padding + innerWidth / 2, y: toY(values[0] ?? min) }]
  }
  const step = innerWidth / (values.length - 1)
  return values.map((value, index) => ({
    x: padding + index * step,
    y: toY(value),
  }))
}

/** Build an SVG polyline path (`M x,y L x,y …`) from points. */
export function toLinePath(points: Point[]): string {
  return points
    .map((point, index) => {
      const command = index === 0 ? 'M' : 'L'
      return `${command}${point.x.toFixed(2)},${point.y.toFixed(2)}`
    })
    .join(' ')
}

/** Close a line path down to `baseline` to form a filled area. */
export function toAreaPath(points: Point[], baseline: number): string {
  const first = points[0]
  const last = points[points.length - 1]
  if (!first || !last) return ''
  return `${toLinePath(points)} L${last.x.toFixed(2)},${baseline} L${first.x.toFixed(2)},${baseline} Z`
}

/**
 * Lay out one radar spoke per value, first spoke pointing straight up and the
 * rest distributed clockwise. `max` is the value at the outer ring.
 */
export function radarSpokes(
  values: number[],
  max: number,
  center: number,
  radius: number,
): Point[] {
  const count = values.length
  if (count === 0) return []
  return values.map((value, index) => {
    const angle = (Math.PI * 2 * index) / count - Math.PI / 2
    const ratio = max <= 0 ? 0 : Math.min(Math.max(value / max, 0), 1)
    const distance = radius * ratio
    return {
      x: center + Math.cos(angle) * distance,
      y: center + Math.sin(angle) * distance,
    }
  })
}

/** The vertices of a regular polygon ring, used for the radar grid. */
export function ringPolygon(count: number, center: number, radius: number): Point[] {
  return Array.from({ length: count }, (_, index) => {
    const angle = (Math.PI * 2 * index) / count - Math.PI / 2
    return {
      x: center + Math.cos(angle) * radius,
      y: center + Math.sin(angle) * radius,
    }
  })
}

/** Render a list of points as an SVG `points` attribute value. */
export function toPointsAttribute(points: Point[]): string {
  return points.map((point) => `${point.x.toFixed(2)},${point.y.toFixed(2)}`).join(' ')
}
