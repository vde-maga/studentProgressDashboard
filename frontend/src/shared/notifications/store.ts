/**
 * Tiny external store for transient, app-wide notifications.
 *
 * React Query's caches push here when a background query or a mutation fails,
 * so failures that have no contextual UI are still surfaced to the user. Kept
 * framework-agnostic; `Toaster` reads it with `useSyncExternalStore`.
 */

export interface Notification {
  id: number
  message: string
}

type Listener = () => void

let notifications: readonly Notification[] = []
const listeners = new Set<Listener>()
let nextId = 1

function emit(): void {
  for (const listener of listeners) listener()
}

/** Push a notification and return its id. */
export function notify(message: string): number {
  const id = nextId++
  notifications = [...notifications, { id, message }]
  emit()
  return id
}

/** Remove a single notification by id. */
export function dismiss(id: number): void {
  const next = notifications.filter((item) => item.id !== id)
  if (next.length === notifications.length) return
  notifications = next
  emit()
}

export function subscribe(listener: Listener): () => void {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

export function getSnapshot(): readonly Notification[] {
  return notifications
}
