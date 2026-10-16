/**
 * Subscribe to the live activity stream (`GET /events/stream`).
 *
 * The endpoint emits a cursor of activity events; `EventSource` reconnects on
 * its own (resuming from `Last-Event-ID`), so this hook only needs to surface
 * the bounded, de-duplicated list of events it has seen.
 */

import { useEffect, useState } from 'react'

import { streamEventsUrl } from '@/shared/api/endpoints'
import type { ActivityEvent, ActivityKind } from '@/shared/api/types'

const KINDS: ActivityKind[] = [
  'login',
  'commit',
  'evaluation_given',
  'evaluation_received',
  'project_validated',
]

export type StreamStatus = 'connecting' | 'open'

export interface ActivityStream {
  events: ActivityEvent[]
  status: StreamStatus
}

export function useActivityStream(limit = 40): ActivityStream {
  const [events, setEvents] = useState<ActivityEvent[]>([])
  const [status, setStatus] = useState<StreamStatus>('connecting')

  useEffect(() => {
    const source = new EventSource(streamEventsUrl())

    const onOpen = () => setStatus('open')
    const onError = () => setStatus('connecting')
    const onEvent = (event: MessageEvent<string>) => {
      let item: ActivityEvent
      try {
        item = JSON.parse(event.data) as ActivityEvent
      } catch {
        return
      }
      setEvents((previous) => {
        if (previous.some((seen) => seen.id === item.id)) return previous
        return [item, ...previous].slice(0, limit)
      })
    }

    source.onopen = onOpen
    source.onerror = onError
    for (const kind of KINDS) {
      source.addEventListener(kind, onEvent as EventListener)
    }
    source.addEventListener('message', onEvent as EventListener)

    return () => source.close()
  }, [limit])

  return { events, status }
}
