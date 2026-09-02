import { useState } from 'react'
import { Activity, AlertTriangle, CheckCircle2, Flame, Radio, RefreshCw, Zap } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { useLiveStream } from '@/hooks/useLiveStream'
import { api } from '@/api/client'

export function LiveEventTicker() {
  const { isConnected, recentEvents, eventCounts } = useLiveStream(true)
  const [injecting, setInjecting] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)

  const handleTriggerChaos = async (scenarioId: string, label: string) => {
    try {
      setInjecting(scenarioId)
      await api.triggerChaosScenario(scenarioId)
      setFeedback(`Cenário '${label}' injetado com sucesso!`)
      setTimeout(() => setFeedback(null), 4000)
    } catch (err) {
      console.error(err)
      setFeedback('Erro ao disparar cenário.')
    } finally {
      setInjecting(null)
    }
  }

  return (
    <Card className="border-indigo-500/30 bg-gradient-to-r from-indigo-950/20 via-background to-purple-950/20 shadow-sm">
      <CardContent className="p-3.5 space-y-3">
        {/* Barra superior de status do Streaming */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2.5">
            <span className="relative flex h-3 w-3">
              {isConnected ? (
                <>
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                </>
              ) : (
                <span className="relative inline-flex rounded-full h-3 w-3 bg-rose-500"></span>
              )}
            </span>
            <span className="text-xs font-bold tracking-wide uppercase flex items-center gap-1.5">
              <Radio size={14} className={isConnected ? 'text-emerald-500 animate-pulse' : 'text-rose-500'} />
              {isConnected ? 'Ingestão em Tempo Real Ativa (SSE)' : 'Aguardando Conexão SSE…'}
            </span>
            <Badge variant="outline" className="text-[10px] font-mono bg-background/80">
              {eventCounts.telemetry + eventCounts.payment + eventCounts.crm + eventCounts.rescores} eventos recebidos
            </Badge>
          </div>

          {/* Botões de injeção de caos em tempo real */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] font-medium text-muted-foreground mr-1 flex items-center gap-1">
              <Zap size={12} className="text-amber-500" /> Injetar Falha ao Vivo:
            </span>
            <Button
              size="sm"
              variant="outline"
              disabled={injecting !== null}
              onClick={() => handleTriggerChaos('fiber_cut', 'Rompimento de Fibra')}
              className="h-7 text-[11px] gap-1 border-rose-500/30 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/50"
            >
              <Flame size={12} />
              {injecting === 'fiber_cut' ? 'Injetando…' : 'Queda de Fibra (SP)'}
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={injecting !== null}
              onClick={() => handleTriggerChaos('payment_gateway_down', 'Falha Gateway PIX')}
              className="h-7 text-[11px] gap-1 border-amber-500/30 text-amber-600 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-950/50"
            >
              <AlertTriangle size={12} />
              {injecting === 'payment_gateway_down' ? 'Injetando…' : 'Falha Gateway PIX'}
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={injecting !== null}
              onClick={() => handleTriggerChaos('crm_crisis', 'Crise de Atendimento')}
              className="h-7 text-[11px] gap-1 border-purple-500/30 text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-950/50"
            >
              <Activity size={12} />
              {injecting === 'crm_crisis' ? 'Injetando…' : 'Crise WhatsApp'}
            </Button>
          </div>
        </div>

        {feedback && (
          <div className="flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400 font-medium bg-emerald-500/10 px-2.5 py-1 rounded">
            <CheckCircle2 size={13} /> {feedback}
          </div>
        )}

        {/* Ticker contínuo com os 3 últimos eventos */}
        <div className="bg-background/90 rounded-md p-2 border text-xs font-mono space-y-1 max-h-24 overflow-y-auto">
          {recentEvents.length === 0 ? (
            <div className="text-muted-foreground text-[11px] flex items-center gap-1.5">
              <RefreshCw size={12} className="animate-spin text-primary" />
              Aguardando primeiros eventos de streaming da rede... (Dica: clique em um botão de falha acima para testar)
            </div>
          ) : (
            recentEvents.slice(0, 4).map((evt, idx) => {
              const isAlert = evt.event_type === 'ALERT'
              const isRescore = evt.event_type === 'RE_SCORE'
              return (
                <div
                  key={idx}
                  className={`flex items-center justify-between gap-2 px-2 py-0.5 rounded text-[11px] ${
                    isAlert
                      ? 'bg-rose-500/15 text-rose-700 dark:text-rose-300 font-semibold animate-pulse'
                      : isRescore
                        ? 'bg-amber-500/10 text-amber-700 dark:text-amber-300'
                        : 'text-muted-foreground'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <span className="font-bold text-[10px] px-1.5 py-0.2 rounded bg-muted">
                      {evt.event_type}
                    </span>
                    <span className="font-semibold text-foreground">{evt.customer_id ?? 'Sistema'}</span>
                    <span className="truncate">
                      {isAlert
                        ? `🚨 ${(evt.data as { reason?: string }).reason ?? 'Alerta Crítico de Churn'}`
                        : isRescore
                          ? `📊 Risco: ${(evt.data as { previous_risk_score?: number }).previous_risk_score ?? 0} ➔ ${(evt.data as { new_risk_score?: number }).new_risk_score ?? 0} (Δ ${(evt.data as { risk_delta?: number }).risk_delta ?? 0})`
                          : JSON.stringify(evt.data)}
                    </span>
                  </div>
                  <span className="text-[10px] text-muted-foreground shrink-0">
                    {new Date(evt.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              )
            })
          )}
        </div>
      </CardContent>
    </Card>
  )
}
