import { describe, expect, it } from 'vitest'

import { formatDay, formatLevel, formatProgress, formatXp } from './format'

describe('formatLevel', () => {
  it('renders a string level to two decimals', () => {
    expect(formatLevel('9.63')).toBe('9.63')
    expect(formatLevel('21')).toBe('21.00')
  })
})

describe('formatXp', () => {
  it('groups thousands', () => {
    expect(formatXp(45000)).toBe('45,000')
    expect(formatXp(7)).toBe('7')
  })
})

describe('formatProgress', () => {
  it('turns a fraction into a whole percentage', () => {
    expect(formatProgress('0.63')).toBe('63%')
    expect(formatProgress(1)).toBe('100%')
  })

  it('clamps out-of-range values', () => {
    expect(formatProgress(-0.5)).toBe('0%')
    expect(formatProgress(2)).toBe('100%')
  })
})

describe('formatDay', () => {
  it('renders an ISO day in UTC', () => {
    expect(formatDay('2026-03-12')).toBe('12 Mar')
  })

  it('returns the input unchanged when unparseable', () => {
    expect(formatDay('not-a-date')).toBe('not-a-date')
  })
})
