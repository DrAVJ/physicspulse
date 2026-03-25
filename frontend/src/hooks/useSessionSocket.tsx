import { useEffect, useRef, useState, useCallback } from 'react'

export type WsMessage = {
  type: string
  [key: string]: unknown
}

export type WsStatus = 'connecting' | 'open' | 'closed' | 'error'

interface UseSessionSocketOptions {
  sessionId: number | null
  studentId?: number | null
  isTeacher?: boolean
  onMessage?: (msg: WsMessage) => void
}

export function useSessionSocket({
  sessionId,
  studentId = null,
  isTeacher = false,
  onMessage,
}: UseSessionSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null)
  const [status, setStatus] = useState<WsStatus>('closed')
  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage

  const connect = useCallback(() => {
    if (!sessionId) return
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const host = window.location.host
    let url: string
    if (isTeacher) {
      url = `${protocol}://${host}/ws/teacher/${sessionId}`
    } else {
      url = `${protocol}://${host}/ws/student/${sessionId}/${studentId}`
    }
    const ws = new WebSocket(url)
    wsRef.current = ws
    setStatus('connecting')

    ws.onopen = () => setStatus('open')
    ws.onclose = () => setStatus('closed')
    ws.onerror = () => setStatus('error')
    ws.onmessage = (event) => {
      try {
        const msg: WsMessage = JSON.parse(event.data)
        onMessageRef.current?.(msg)
      } catch (e) {
        console.error('WS parse error', e)
      }
    }
  }, [sessionId, studentId, isTeacher])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
    }
  }, [connect])

  const send = useCallback((msg: WsMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg))
    }
  }, [])

  return { status, send }
}
