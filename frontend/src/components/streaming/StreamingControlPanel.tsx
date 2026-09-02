import { useState, useEffect } from 'react'
import {
  Activity,
  Play,
  Square,
  Flame,
  Radio,
  Wifi,
  CreditCard,
  Headphones,
  RefreshCw,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { api } from '@/api/client'
import type { StreamingStatusResponse } from '@/types'

export function StreamingControlPanel() {
  const [status, setStatus] = useState<StreamingStatusResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [eventsPerSec, setEventsPerSec] = useState(5)

  const fetchStatus = async () => {
    try {
      const data = await api.getStreamingStatus()
      setStatus(data)
      setEventsPerSec(data.events_per_second)
    } catch (err) {
      console.error('Falha ao carregar status do streaming:', err)
    }
  }

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 2000)
    return () => clearInterval(interval)
  }, [])

  const handleToggleRunning = async () => {
    setLoading(true)
    try {
      if (status?.is_running) {
        const updated = await api.stopStreaming()
        setStatus(updated)
      } else {
        const updated = await api.startStreaming({ events_per_second: eventsPerSec })
        setStatus(updated)
      }
    } catch (err) {
      console.error('Erro ao alterar streaming:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleToggleChaos = async () => {
    if (!status) return
    setLoading(true)
    try {
      const updated = await api.injectStreamingChaos({
        enable_chaos: !status.chaos_mode,
      })
      setStatus(updated)
    } catch (err) {
      console.error('Erro ao alternar modo caos:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Banner & Controls */}
      <Card className="border-border bg-card">
        <CardHeader className="pb-3">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <Radio className={`h-5 w-5 ${status?.is_running ? 'text-emerald-500 animate-pulse' : 'text-muted-foreground'}`} />
                <CardTitle className="text-lg font-bold">Gerador Contínuo de Eventos em Streaming (Fase 3)</CardTitle>
                {status?.is_running ? (
                  <Badge variant="outline" className="bg-emerald-500/10 text-emerald-600 border-emerald-500/30">
                    ● Streaming Ativo ({status.events_per_second} evt/s)
                  </Badge>
                ) : (
                  <Badge variant="outline" className="bg-slate-500/10 text-slate-500 border-slate-500/30">
                    ○ Em Pausa
                  </Badge>
                )}
                {status?.chaos_mode && (
                  <Badge variant="destructive" className="animate-pulse">
                    🔥 Modo Caos Ativado
                  </Badge>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Emite eventos sintéticos em tempo real simulando telemetria de rede, cobrança e CRM para tópicos Kafka/Redpanda.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Button
                variant={status?.is_running ? 'destructive' : 'default'}
                size="sm"
                onClick={handleToggleRunning}
                disabled={loading}
                className="gap-1.5"
              >
                {status?.is_running ? (
                  <>
                    <Square className="h-4 w-4 fill-current" /> Pausar Streaming
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 fill-current" /> Iniciar Streaming
                  </>
                )}
              </Button>

              <Button
                variant={status?.chaos_mode ? 'destructive' : 'outline'}
                size="sm"
                onClick={handleToggleChaos}
                disabled={loading}
                className="gap-1.5"
                title="Injeta instabilidade massiva de fibra e falhas de pagamento em lote"
              >
                <Flame className={`h-4 w-4 ${status?.chaos_mode ? 'text-amber-300' : 'text-amber-500'}`} />
                {status?.chaos_mode ? 'Desativar Caos' : 'Injetar Caos'}
              </Button>

              <Button variant="ghost" size="icon" onClick={fetchStatus} title="Atualizar agora">
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            {/* Tópico 1: Telemetria */}
            <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-md bg-blue-500/10 text-blue-500">
                  <Wifi className="h-5 w-5" />
                </div>
                <div>
                  <div className="text-xs font-semibold text-muted-foreground">telemetry.network.events</div>
                  <div className="text-xl font-bold font-mono">
                    {status?.total_generated?.['telemetry.network.events']?.toLocaleString() ?? 0}
                  </div>
                </div>
              </div>
              <Badge variant="secondary" className="text-[10px]">70% mix</Badge>
            </div>

            {/* Tópico 2: Faturamento */}
            <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-md bg-emerald-500/10 text-emerald-500">
                  <CreditCard className="h-5 w-5" />
                </div>
                <div>
                  <div className="text-xs font-semibold text-muted-foreground">billing.payment.events</div>
                  <div className="text-xl font-bold font-mono">
                    {status?.total_generated?.['billing.payment.events']?.toLocaleString() ?? 0}
                  </div>
                </div>
              </div>
              <Badge variant="secondary" className="text-[10px]">15% mix</Badge>
            </div>

            {/* Tópico 3: CRM */}
            <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-md bg-purple-500/10 text-purple-500">
                  <Headphones className="h-5 w-5" />
                </div>
                <div>
                  <div className="text-xs font-semibold text-muted-foreground">crm.interaction.events</div>
                  <div className="text-xl font-bold font-mono">
                    {status?.total_generated?.['crm.interaction.events']?.toLocaleString() ?? 0}
                  </div>
                </div>
              </div>
              <Badge variant="secondary" className="text-[10px]">15% mix</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Live Event Stream Table / Inspector */}
      <Card className="border-border bg-card">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <Activity className="h-4 w-4 text-primary" />
              Feed de Eventos em Tempo Real (Últimos gerados)
            </CardTitle>
            <span className="text-xs text-muted-foreground">
              Buffer ativo: {status?.buffer_size ?? 0} eventos
            </span>
          </div>
        </CardHeader>
        <CardContent>
          {status?.recent_events && status.recent_events.length > 0 ? (
            <div className="space-y-2 font-mono text-xs max-h-72 overflow-y-auto pr-1">
              {status.recent_events.slice().reverse().map((evt, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded bg-slate-900 text-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-2 border border-slate-800"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-cyan-400 font-semibold">{String(evt.topic)}</span>
                    <span className="text-slate-500">|</span>
                    <span className="text-amber-300 font-bold">{String(evt.customer_id)}</span>
                    <span className="text-slate-500">|</span>
                    <span className="text-emerald-400 font-bold">
                      {String(evt.event_type || evt.reason || 'EVENT')}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400">
                    {String(evt.timestamp || '')}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-muted-foreground">
              Nenhum evento no buffer. Clique em <b>Iniciar Streaming</b> para começar a gerar fluxo contínuo.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
