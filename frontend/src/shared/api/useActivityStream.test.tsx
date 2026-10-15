import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { ActivityEvent } from '@/shared/api/types'
import { useActivityStream } from './useActivityStream'

class FakeEventSource {
  static instances: FakeEventSource[] = []

  onopen: (() => void) | null = null
  onerror: (() => void) | null = null
  closed = false
  readonly url: string
  private readonly listeners = new Map<string, ((event: MessageEvent) => void)[]>()

  constructor(url: string) {
    this.url = url
    FakeEventSource.instances.push(this)
  }

  addEventListener(type: string, callback: EventListenerOrEventListenerObject) {
    const list = this.listeners.get(type) ?? []
    list.push(callback as (event: MessageEvent) => void)
    this.listeners.set(type, list)
  }

  close() {
    this.closed = true
  }

  emit(type: string, data: unknown) {
    const list = this.listeners.get(type) ?? []
    for (const callback of list) {
      callback(new MessageEvent('message', { data: JSON.stringify(data) }))
    }
  }

  open() {
    this.onopen?.()
  }
}

function event(id: number): ActivityEvent {
  return {
    id,
    kind: 'commit',
    student_login: 'ada',
    day: '2026-03-12',
    xp_delta: 100,
    project_slug: 'push_swap',
    occurred_at: '2026-03-12T09:00:00Z',
  }
}

beforeEach(() => {
  FakeEventSource.instances = []
  vi.stubGlobal('EventSource', FakeEventSource)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

function latest(): FakeEventSource {
  const instance = FakeEventSource.instances.at(-1)
  if (!instance) throw new Error('no EventSource was constructed')
  return instance
}

describe('useActivityStream', () => {
  it('opens a stream and reports the connection', () => {
    const { result } = renderHook(() => useActivityStream())
    expect(result.current.status).toBe('connecting')

    act(() => latest().open())
    expect(result.current.status).toBe('open')
  })

  it('prepends new events', () => {
    const { result } = renderHook(() => useActivityStream())

    act(() => latest().emit('commit', event(1)))
    act(() => latest().emit('commit', event(2)))

    expect(result.current.events.map((item) => item.id)).toEqual([2, 1])
  })

  it('ignores duplicate event ids', () => {
    const { result } = renderHook(() => useActivityStream())

    act(() => latest().emit('commit', event(1)))
    act(() => latest().emit('commit', event(1)))

    expect(result.current.events).toHaveLength(1)
  })

  it('caps the buffered list at the given limit', () => {
    const { result } = renderHook(() => useActivityStream(2))

    act(() => latest().emit('commit', event(1)))
    act(() => latest().emit('commit', event(2)))
    act(() => latest().emit('commit', event(3)))

    expect(result.current.events.map((item) => item.id)).toEqual([3, 2])
  })

  it('closes the stream on unmount', () => {
    const { unmount } = renderHook(() => useActivityStream())
    const instance = latest()

    unmount()

    expect(instance.closed).toBe(true)
  })
})
