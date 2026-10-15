/** Presentation helpers for the numeric values the API returns as strings. */

/** Format a level (0-21) to two decimals, e.g. `"9.63"`. */
export function formatLevel(level: string | number): string {
  return Number(level).toFixed(2)
}

/** Format an XP total with thousands separators, e.g. `"12,450"`. */
export function formatXp(xp: number): string {
  return new Intl.NumberFormat('en-US').format(xp)
}

/** Format a 0-1 level-progress fraction as a whole percentage, e.g. `"63%"`. */
export function formatProgress(fraction: string | number): string {
  const value = Number(fraction)
  const clamped = Number.isFinite(value) ? Math.min(Math.max(value, 0), 1) : 0
  return `${Math.round(clamped * 100)}%`
}

/** Render a date-only string as a short, human label, e.g. `"12 Mar"`. */
export function formatDay(day: string): string {
  const date = new Date(`${day}T00:00:00Z`)
  if (Number.isNaN(date.getTime())) return day
  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    timeZone: 'UTC',
  })
}
