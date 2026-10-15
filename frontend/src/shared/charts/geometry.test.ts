import { describe, expect, it } from 'vitest'

import {
  radarSpokes,
  ringPolygon,
  scaleSeries,
  toLinePath,
  toPointsAttribute,
  type Point,
} from './geometry'

describe('scaleSeries', () => {
  it('returns nothing for an empty series', () => {
    expect(scaleSeries([], 100, 50)).toEqual([])
  })

  it('puts the lowest value on the baseline and the highest at the top', () => {
    const points = scaleSeries([0, 100], 100, 50)
    expect(points[0]).toEqual({ x: 0, y: 50 })
    expect(points[1]).toEqual({ x: 100, y: 0 })
  })

  it('spreads points evenly across the width', () => {
    const points = scaleSeries([1, 2, 3], 100, 50)
    expect(points.map((point) => point.x)).toEqual([0, 50, 100])
  })

  it('centres a single point horizontally', () => {
    expect(scaleSeries([5], 100, 50)).toEqual([{ x: 50, y: 0 }])
  })

  it('applies padding on all sides', () => {
    const points = scaleSeries([0, 10], 100, 100, 10)
    expect(points[0]).toEqual({ x: 10, y: 90 })
    expect(points[1]).toEqual({ x: 90, y: 10 })
  })
})

describe('toLinePath', () => {
  it('emits a move then line commands', () => {
    const points: Point[] = [
      { x: 0, y: 0 },
      { x: 10, y: 20 },
    ]
    expect(toLinePath(points)).toBe('M0.00,0.00 L10.00,20.00')
  })

  it('is empty for no points', () => {
    expect(toLinePath([])).toBe('')
  })
})

describe('radarSpokes', () => {
  it('puts the first spoke straight up', () => {
    const [first] = radarSpokes([1], 1, 50, 40)
    expect(first?.x).toBeCloseTo(50)
    expect(first?.y).toBeCloseTo(10)
  })

  it('scales the spoke length by the value ratio', () => {
    const [half] = radarSpokes([0.5], 1, 50, 40)
    expect(half?.y).toBeCloseTo(30)
  })

  it('clamps values above the maximum to the outer ring', () => {
    const [over] = radarSpokes([5], 1, 50, 40)
    expect(over?.y).toBeCloseTo(10)
  })
})

describe('ringPolygon', () => {
  it('produces one vertex per count', () => {
    expect(ringPolygon(4, 50, 40)).toHaveLength(4)
  })
})

describe('toPointsAttribute', () => {
  it('joins points with commas and spaces', () => {
    const points: Point[] = [
      { x: 1, y: 2 },
      { x: 3, y: 4 },
    ]
    expect(toPointsAttribute(points)).toBe('1.00,2.00 3.00,4.00')
  })
})
