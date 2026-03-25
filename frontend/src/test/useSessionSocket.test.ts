import { describe, it, expect } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useSessionSocket } from '../hooks/useSessionSocket'

// Mock WebSocket
class MockWebSocket {
  onopen: (() => void) | null = null
  onclose: (() => void) | null = null
  onerror: (() => void) | null = null
  onmessage: ((e: { data: string }) => void) | null = null
  readyState = WebSocket.CONNECTING
  close() { this.onclose?.() }
  send(_data: string) {}
}

global.WebSocket = MockWebSocket as unknown as typeof WebSocket

describe('useSessionSocket', () => {
  it('returns closed status when sessionId is null', () => {
    const { result } = renderHook(() =>
      useSessionSocket({ sessionId: null })
    )
    expect(result.current.status).toBe('closed')
  })

  it('exposes a send function', () => {
    const { result } = renderHook(() =>
      useSessionSocket({ sessionId: null })
    )
    expect(typeof result.current.send).toBe('function')
  })
})
