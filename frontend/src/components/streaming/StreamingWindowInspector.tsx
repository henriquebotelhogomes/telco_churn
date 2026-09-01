import { useState, useEffect } from 'react'
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Radio,
  RefreshCw,
  ShieldAlert,
  Zap,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { api } from '@/api/client'
import type { CustomerWindowMetrics, RealtimeRiskAlert } from '@/types'

export function StreamingWindowInspector() {
  const [windows, setWindows] = useState<CustomerWindowMetrics[]>([])
  const [alerts, setAlerts] = useState<RealtimeRiskAlert[]>([])
  const [acknowledgingId, setAcknowledgingId] = useState<string | null>(null)

  const fetchData = async () => {
    try {
      const [windowsRes, alertsRes] = await Promise.all([
        api.listStreamingWindows(20),
        api.listRealtimeAlerts(10),
      ])
      setWindows(windowsRes.windows || [])
      setAlerts(alertsRes.alerts || [])
    } catch (err) {
      console.error('Erro ao carregar janelas de streaming:', err)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 2500)
    return () => clearInterval(interval)
  }, [])

  const handleAcknowledge = async (alertId: string) => {
    setAcknowledgingId(alertId)
    try {
      await api.acknowledgeAlert(alertId, 'analista_retencao')
      await fetchData()
    } catch (err) {
      console.error('Erro ao reconhecer alerta:', err)
    } finally {
      setAcknowledgingId(null)
    }
  }

  const getInstabilityColor = (score: number) => {
    if (score >= 0.7) return 'bg-red-500/15 text-red-600 border-red-500/30'
    if (score >= 0.4) return 'bg-amber-500/15 text-amber-600 border-amber-500/30'
    return 'bg-emerald-500/15 text-emerald-600 border-emerald-500/30'
  }

  return (
    <div className="space-y-6">
      {/* 1. Feed de Alertas Reativos em Tempo Real */}
      <Card className="border-border bg-card">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-amber-500" />
              <CardTitle className="text-base font-bold">
                Fila de Alertas Reativos de Churn (SLA &lt; 100ms)
              </CardTitle>
              {alerts.length > 0 ? (
                <Badge variant="destructive" className="animate-pulse">
                  {alerts.filter((a) => !a.acknowledged).length} Pendentes
                </Badge>
              ) : (
                <Badge variant="outline" className="bg-emerald-500/10 text-emerald-600">
                  ✓ Sem Alertas Críticos
                </Badge>
              )}
            </div>
            <Button variant="ghost" size="sm" onClick={fetchData} className="gap-1 text-xs">
              <RefreshCw className="h-3.5 w-3.5" /> Atualizar
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            Disparados imediatamente quando um cliente ultrapassa limiares de risco em janelas deslizantes (ex: &ge; 3 quedas/hora ou falha financeira com reclamação).
          </p>
        </CardHeader>
        <CardContent>
          {alerts.length > 0 ? (
            <div className="space-y-3">
              {alerts.map((alert) => (
                <div
                  key={alert.alert_id}
                  className={`p-3.5 rounded-lg border flex flex-col md:flex-row md:items-center justify-between gap-3 ${
                    alert.acknowledged
                      ? 'bg-slate-50/50 dark:bg-slate-900/30 border-slate-200 dark:border-slate-800 opacity-60'
                      : alert.severity === 'CRITICA'
                        ? 'bg-red-500/5 border-red-500/20'
                        : 'bg-amber-500/5 border-amber-500/20'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge
                        variant={alert.severity === 'CRITICA' ? 'destructive' : 'default'}
                        className="text-[10px] uppercase font-bold"
                      >
                        {alert.severity}
                      </Badge>
                      <span className="font-mono font-bold text-sm text-foreground">
                        {alert.customer_id}
                      </span>
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {new Date(alert.created_at).toLocaleTimeString()}
                      </span>
                      <Badge variant="outline" className={getInstabilityColor(alert.instability_score)}>
                        Score: {alert.instability_score.toFixed(2)}
                      </Badge>
                    </div>
                    <div className="text-xs font-medium text-foreground">
                      {alert.trigger_reason}
                    </div>
                    <div className="text-xs text-primary font-medium flex items-center gap-1">
                      <Zap className="h-3.5 w-3.5 text-amber-500" />
                      <b>Recomendação:</b> {alert.recommended_intervention}
                    </div>
                  </div>

                  <div className="shrink-0">
                    {alert.acknowledged ? (
                      <span className="text-xs font-semibold text-emerald-600 flex items-center gap-1">
                        <CheckCircle2 className="h-4 w-4" /> Tratado ({alert.acknowledged_by})
                      </span>
                    ) : (
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={acknowledgingId === alert.alert_id}
                        onClick={() => handleAcknowledge(alert.alert_id)}
                        className="gap-1.5 text-xs font-semibold hover:bg-emerald-500/10 hover:text-emerald-600 hover:border-emerald-500/30"
                      >
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        Tratar Alerta
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-6 text-center text-xs text-muted-foreground">
              Nenhum alerta disparado. Inicie o streaming no painel acima para simular a chegada de eventos e disparar gatilhos reativos.
            </div>
          )}
        </CardContent>
      </Card>

      {/* 2. Tabela de Janelas Deslizantes em Tempo Real (Sliding Windows) */}
      <Card className="border-border bg-card">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Radio className="h-4 w-4 text-primary" />
              <CardTitle className="text-base font-bold">
                Agregações em Janelas Deslizantes por Cliente (Flink Engine)
              </CardTitle>
            </div>
            <span className="text-xs text-muted-foreground font-mono">
              {windows.length} clientes em monitoramento ativo
            </span>
          </div>
          <p className="text-xs text-muted-foreground">
            Métricas estocásticas computadas em tempo real sob janelas móveis de 15 minutos, 1 hora, 24 horas e 7 dias.
          </p>
        </CardHeader>
        <CardContent>
          {windows.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-xs font-mono">
                <thead>
                  <tr className="border-b border-border text-muted-foreground text-left">
                    <th className="py-2.5 px-3">Cliente ID</th>
                    <th className="py-2.5 px-3">Instabilidade</th>
                    <th className="py-2.5 px-3">Latência (15m)</th>
                    <th className="py-2.5 px-3">Perda Pacotes (15m)</th>
                    <th className="py-2.5 px-3">Quedas (1h)</th>
                    <th className="py-2.5 px-3">Falhas Cobrança (24h)</th>
                    <th className="py-2.5 px-3">Sentimento (7d)</th>
                    <th className="py-2.5 px-3 text-right">Eventos Acum.</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {windows.map((w) => (
                    <tr key={w.customer_id} className="hover:bg-muted/40 transition-colors">
                      <td className="py-2 px-3 font-bold text-foreground">
                        {w.customer_id}
                      </td>
                      <td className="py-2 px-3">
                        <Badge variant="outline" className={getInstabilityColor(w.realtime_instability_score)}>
                          {w.realtime_instability_score.toFixed(2)}
                        </Badge>
                      </td>
                      <td className="py-2 px-3">
                        <span className={w.avg_latency_15min > 100 ? 'text-red-500 font-bold' : ''}>
                          {w.avg_latency_15min} ms
                        </span>
                      </td>
                      <td className="py-2 px-3">
                        <span className={w.avg_packet_loss_15min > 5 ? 'text-amber-500 font-bold' : ''}>
                          {w.avg_packet_loss_15min}%
                        </span>
                      </td>
                      <td className="py-2 px-3">
                        {w.disconnect_count_1h > 0 ? (
                          <span className="text-red-500 font-bold flex items-center gap-1">
                            <AlertTriangle className="h-3 w-3" /> {w.disconnect_count_1h}
                          </span>
                        ) : (
                          <span className="text-slate-400">0</span>
                        )}
                      </td>
                      <td className="py-2 px-3">
                        {w.failed_payment_count_24h > 0 ? (
                          <span className="text-amber-500 font-bold">
                            {w.failed_payment_count_24h}x
                          </span>
                        ) : (
                          <span className="text-slate-400">0</span>
                        )}
                      </td>
                      <td className="py-2 px-3">
                        <span
                          className={
                            w.avg_sentiment_7d < -0.3
                              ? 'text-red-500 font-bold'
                              : w.avg_sentiment_7d > 0.3
                                ? 'text-emerald-500'
                                : 'text-slate-400'
                          }
                        >
                          {w.avg_sentiment_7d.toFixed(2)} ({w.negative_crm_count_7d} neg)
                        </span>
                      </td>
                      <td className="py-2 px-3 text-right text-muted-foreground">
                        {w.total_events_processed}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-muted-foreground">
              Aguardando eventos para popular as janelas deslizantes...
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
