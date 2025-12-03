/**
 * WebSocket Hook for Sahool Yemen
 * سهول اليمن - خطاف الاتصال المباشر
 *
 * Real-time data updates via WebSocket connection.
 */
import { useEffect, useRef, useState, useCallback } from 'react'

type MessageHandler = (data: any) => void

interface WebSocketMessage {
  type: string
  data: any
  timestamp: number
  channel?: string
}

interface UseWebSocketOptions {
  url?: string
  autoConnect?: boolean
  reconnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Event) => void
}

interface UseWebSocketReturn {
  isConnected: boolean
  isConnecting: boolean
  lastMessage: WebSocketMessage | null
  error: Event | null
  connect: () => void
  disconnect: () => void
  send: (message: WebSocketMessage) => void
  subscribe: (channel: string) => void
  unsubscribe: (channel: string) => void
  on: (type: string, handler: MessageHandler) => () => void
}

/**
 * Custom hook for WebSocket connection
 */
export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    url = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`,
    autoConnect = true,
    reconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
    onConnect,
    onDisconnect,
    onError,
  } = options

  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const [error, setError] = useState<Event | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const handlersRef = useRef<Map<string, Set<MessageHandler>>>(new Map())
  const reconnectAttemptRef = useRef(0)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // Generate client ID
  const clientIdRef = useRef(`client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)

  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
  }, [])

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    setIsConnecting(true)
    setError(null)

    try {
      const wsUrl = `${url}/${clientIdRef.current}`
      wsRef.current = new WebSocket(wsUrl)

      wsRef.current.onopen = () => {
        setIsConnected(true)
        setIsConnecting(false)
        reconnectAttemptRef.current = 0
        onConnect?.()
        console.log('WebSocket connected')
      }

      wsRef.current.onclose = () => {
        setIsConnected(false)
        setIsConnecting(false)
        onDisconnect?.()
        console.log('WebSocket disconnected')

        // Attempt reconnect
        if (reconnect && reconnectAttemptRef.current < maxReconnectAttempts) {
          reconnectAttemptRef.current += 1
          console.log(`Reconnecting... (attempt ${reconnectAttemptRef.current})`)

          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectInterval * Math.min(reconnectAttemptRef.current, 5))
        }
      }

      wsRef.current.onerror = (event) => {
        setError(event)
        onError?.(event)
        console.error('WebSocket error:', event)
      }

      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          setLastMessage(message)

          // Call registered handlers
          const handlers = handlersRef.current.get(message.type)
          if (handlers) {
            handlers.forEach((handler) => handler(message.data))
          }

          // Also call 'all' handlers
          const allHandlers = handlersRef.current.get('*')
          if (allHandlers) {
            allHandlers.forEach((handler) => handler(message))
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e)
        }
      }
    } catch (e) {
      setIsConnecting(false)
      console.error('Failed to create WebSocket:', e)
    }
  }, [url, reconnect, reconnectInterval, maxReconnectAttempts, onConnect, onDisconnect, onError])

  const disconnect = useCallback(() => {
    clearReconnectTimeout()
    reconnectAttemptRef.current = maxReconnectAttempts // Prevent reconnection

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [clearReconnectTimeout, maxReconnectAttempts])

  const send = useCallback((message: WebSocketMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket not connected, message not sent')
    }
  }, [])

  const subscribe = useCallback((channel: string) => {
    send({
      type: 'subscribe',
      data: { channel },
      timestamp: Date.now(),
    })
  }, [send])

  const unsubscribe = useCallback((channel: string) => {
    send({
      type: 'unsubscribe',
      data: { channel },
      timestamp: Date.now(),
    })
  }, [send])

  const on = useCallback((type: string, handler: MessageHandler) => {
    if (!handlersRef.current.has(type)) {
      handlersRef.current.set(type, new Set())
    }
    handlersRef.current.get(type)!.add(handler)

    // Return unsubscribe function
    return () => {
      handlersRef.current.get(type)?.delete(handler)
    }
  }, [])

  // Auto connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [autoConnect, connect, disconnect])

  return {
    isConnected,
    isConnecting,
    lastMessage,
    error,
    connect,
    disconnect,
    send,
    subscribe,
    unsubscribe,
    on,
  }
}

/**
 * Hook for subscribing to a specific channel
 */
export function useChannel<T = any>(channel: string) {
  const [data, setData] = useState<T | null>(null)
  const { isConnected, subscribe, unsubscribe, on } = useWebSocket()

  useEffect(() => {
    if (!isConnected) return

    // Subscribe to channel
    subscribe(channel)

    // Listen for messages on this channel
    const unsubscribeHandler = on('*', (message: WebSocketMessage) => {
      if (message.channel === channel) {
        setData(message.data)
      }
    })

    return () => {
      unsubscribe(channel)
      unsubscribeHandler()
    }
  }, [isConnected, channel, subscribe, unsubscribe, on])

  return { data, isConnected }
}

/**
 * Hook for weather updates
 */
export function useWeatherUpdates(regionId: number) {
  return useChannel<{
    temperature: number
    humidity: number
    conditions: string
    updated_at: string
  }>(`weather:${regionId}`)
}

/**
 * Hook for NDVI updates
 */
export function useNDVIUpdates(fieldId: number) {
  return useChannel<{
    ndvi: number
    status: string
    updated_at: string
  }>(`field:${fieldId}`)
}

/**
 * Hook for alerts
 */
export function useAlerts() {
  const [alerts, setAlerts] = useState<any[]>([])
  const { isConnected, subscribe, unsubscribe, on } = useWebSocket()

  useEffect(() => {
    if (!isConnected) return

    subscribe('alerts')

    const unsubscribeAlert = on('alert', (data) => {
      setAlerts((prev) => [data, ...prev].slice(0, 50)) // Keep last 50 alerts
    })

    const unsubscribeWeatherAlert = on('weather_alert', (data) => {
      setAlerts((prev) => [{ type: 'weather', ...data }, ...prev].slice(0, 50))
    })

    return () => {
      unsubscribe('alerts')
      unsubscribeAlert()
      unsubscribeWeatherAlert()
    }
  }, [isConnected, subscribe, unsubscribe, on])

  const clearAlerts = useCallback(() => setAlerts([]), [])

  return { alerts, clearAlerts, isConnected }
}

/**
 * Hook for notifications
 */
export function useNotifications() {
  const [notifications, setNotifications] = useState<any[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const { isConnected, on } = useWebSocket()

  useEffect(() => {
    if (!isConnected) return

    const unsubscribe = on('notification', (data) => {
      setNotifications((prev) => [{ ...data, read: false }, ...prev].slice(0, 100))
      setUnreadCount((prev) => prev + 1)
    })

    return unsubscribe
  }, [isConnected, on])

  const markAsRead = useCallback((id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    )
    setUnreadCount((prev) => Math.max(0, prev - 1))
  }, [])

  const markAllAsRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
    setUnreadCount(0)
  }, [])

  const clearAll = useCallback(() => {
    setNotifications([])
    setUnreadCount(0)
  }, [])

  return {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    clearAll,
    isConnected,
  }
}

export default useWebSocket
