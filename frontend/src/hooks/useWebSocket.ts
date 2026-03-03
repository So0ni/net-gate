import { useEffect, useRef } from 'react'

type WsMessage = { event: string; data: unknown }
type Handler = (msg: WsMessage) => void

export function useWebSocket(onMessage: Handler) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimerRef = useRef<number | null>(null)
  const connectRef = useRef<() => void>(() => {})
  const handlerRef = useRef(onMessage)
  const unmountedRef = useRef(false)

  useEffect(() => {
    handlerRef.current = onMessage
  }, [onMessage])

  useEffect(() => {
    unmountedRef.current = false
    connectRef.current = () => {
      if (unmountedRef.current) return

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
        if (!unmountedRef.current) {
          reconnectTimerRef.current = window.setTimeout(() => {
            connectRef.current()
          }, 3000)
        }
      }

      wsRef.current = ws
    }

    connectRef.current()
    return () => {
      unmountedRef.current = true
      if (reconnectTimerRef.current !== null) {
        window.clearTimeout(reconnectTimerRef.current)
      }
      wsRef.current?.close()
    }
  }, [])
}
