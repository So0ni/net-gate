import { useEffect, useRef, useCallback } from 'react'

type WsMessage = { event: string; data: unknown }
type Handler = (msg: WsMessage) => void

export function useWebSocket(onMessage: Handler) {
  const wsRef = useRef<WebSocket | null>(null)
  const handlerRef = useRef(onMessage)
  handlerRef.current = onMessage

  const connect = useCallback(() => {
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(`${protocol}://${location.host}/ws`)

    ws.onmessage = (e) => {
      try {
        const msg: WsMessage = JSON.parse(e.data)
        handlerRef.current(msg)
      } catch {
        // ignore malformed messages
      }
    }

    ws.onclose = () => {
      // Reconnect after 3s
      setTimeout(connect, 3000)
    }

    wsRef.current = ws
  }, [])

  useEffect(() => {
    connect()
    return () => wsRef.current?.close()
  }, [connect])
}
