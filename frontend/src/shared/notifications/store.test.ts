import { beforeEach, describe, expect, it, vi } from 'vitest'

import { dismiss, getSnapshot, notify, subscribe } from './store'

beforeEach(() => {
  // Drain any notifications left by previous tests.
  for (const item of getSnapshot()) dismiss(item.id)
})

describe('notification store', () => {
  it('appends notifications and notifies subscribers', () => {
    const listener = vi.fn()
    const unsubscribe = subscribe(listener)

    notify('first')
    notify('second')

    expect(getSnapshot().map((n) => n.message)).toEqual(['first', 'second'])
    expect(listener).toHaveBeenCalledTimes(2)
    unsubscribe()
  })

  it('dismisses a single notification by id', () => {
    const id = notify('keep me')
    notify('remove me')

    dismiss(id)

    expect(getSnapshot().map((n) => n.message)).toEqual(['remove me'])
  })

  it('stops notifying after unsubscribe', () => {
    const listener = vi.fn()
    subscribe(listener)()

    notify('silent')

    expect(listener).not.toHaveBeenCalled()
  })
})
