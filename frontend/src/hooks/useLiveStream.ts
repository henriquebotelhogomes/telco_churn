import { useState, useEffect, useRef, useCallback } from 'react'
import { getTenantId } from '@/api/client'

export interface LiveEventPayload {
  event_type: 'TELEMETRY' | 'PAYMENT' | 'CRM' | 'RE_SCORE' | 'ALERT' | 'HEARTBEAT'
  tenant_id: string
  customer_id?: string
  data: Record<string, unknown>
  timestamp: string
}

export interface LiveCustomerScore {
  customer_id: string
  tenant_id: string
  previous_risk_score: number
  new_risk_score: number
  risk_delta: number
  risk_level: 'Baixo' | 'Médio' | 'Alto' | 'Crítico'
  reasons: string[]
  recommended_action: string
  updated_at: string
}

export function useLiveStream(enabled: boolean = true) {
  const [isConnected, setIsConnected] = useState(false)
  const [recentEvents, setRecentEvents] = useState<LiveEventPayload[]>([])
  const [liveScores, setLiveScores] = useState<Record<string, LiveCustomerScore>>({})
  const [eventCounts, setEventCounts] = useState({
    telemetry: 0,
    payment: 0,
    crm: 0,
    alerts: 0,
    rescores: 0,
  })

  const eventSourceRef = useRef<EventSource | null>(null)
  const activeTenant = getTenantId()

  const connect = useCallback(() => {
    if (!enabled) return

    const baseUrl = import.meta.env.VITE_API_BASE_URL ?? ''
    const url = `${baseUrl}/api/v1/streaming/live-feed?tenant_id=${encodeURIComponent(activeTenant)}`

    const es = new EventSource(url)
    eventSourceRef.current = es

    es.onopen = () => {
      setIsConnected(true)
    }

    es.onmessage = (event) => {
      try {
        const payload: LiveEventPayload = JSON.parse(event.data)

        if (payload.event_type === 'HEARTBEAT') return

        setRecentEvents((prev) => [payload, ...prev.slice(0, 49)])

        // Atualiza contadores
        setEventCounts((c) => ({
          ...c,
          telemetry: payload.event_type === 'TELEMETRY' ? c.telemetry + 1 : c.telemetry,
          payment: payload.event_type === 'PAYMENT' ? c.payment + 1 : c.payment,
          crm: payload.event_type === 'CRM' ? c.crm + 1 : c.crm,
          alerts: payload.event_type === 'ALERT' ? c.alerts + 1 : c.alerts,
          rescores: payload.event_type === 'RE_SCORE' ? c.rescores + 1 : c.rescores,
        }))

        // Se for atualização de risco
        if (payload.event_type === 'RE_SCORE' && payload.customer_id) {
          const scoreData = payload.data as unknown as LiveCustomerScore
          setLiveScores((prev) => ({
            ...prev,
            [payload.customer_id!]: scoreData,
          }))
        }
      } catch (err) {
        console.debug('Erro ao processar SSE message:', err)
      }
    }

    es.onerror = () => {
      setIsConnected(false)
      es.close()
      // Tenta reconectar em 3 segundos
      setTimeout(() => {
        if (enabled) connect()
      }, 3000)
    }
  }, [enabled, activeTenant])

  useEffect(() => {
    if (enabled) {
      connect()
    }
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
        setIsConnected(false)
      }
    }
  }, [enabled, connect])

  return {
    isConnected,
    recentEvents,
    liveScores,
    eventCounts,
  }
}
