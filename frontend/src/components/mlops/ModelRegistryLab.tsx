import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Trophy,
  Swords,
  Gauge,
  CheckCircle2,
  ArrowUpRight,
  RefreshCw,
  Zap,
} from 'lucide-react'

import { api } from '@/api/client'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import type { ModelRegistryItem } from '@/types'

export function ModelRegistryLab() {
  const queryClient = useQueryClient()
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const modelsQuery = useQuery({
    queryKey: ['model-registry'],
    queryFn: () => api.listModels(),
  })

  const shadowQuery = useQuery({
    queryKey: ['shadow-metrics'],
    queryFn: () => api.shadowMetrics(),
    refetchInterval: 10_000,
  })

  const promoteMutation = useMutation({
    mutationFn: (modelName: string) => api.promoteModel(modelName),
    onSuccess: (data) => {
      setSuccessMsg(`Modelo '${data.new_champion}' promovido para Champion com sucesso!`)
      queryClient.invalidateQueries({ queryKey: ['model-registry'] })
      queryClient.invalidateQueries({ queryKey: ['model-info'] })
      queryClient.invalidateQueries({ queryKey: ['shadow-metrics'] })
      setTimeout(() => setSuccessMsg(null), 5000)
    },
  })

  if (modelsQuery.isLoading) {
    return <Skeleton className="h-96 w-full" />
  }

  const registry = modelsQuery.data
  const activeChampionName = registry?.active_champion
  const models = registry?.models ?? []
  const shadowData = shadowQuery.data

  return (
    <div className="space-y-6">
      {/* Top Banner de Sucesso */}
      {successMsg && (
        <div className="flex items-center gap-2 rounded-lg bg-emerald-500/15 p-4 text-sm font-medium text-emerald-800 dark:text-emerald-300">
          <CheckCircle2 size={18} />
          {successMsg}
        </div>
      )}

      {/* Seção 1: Champion vs Challengers Cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        {models.map((model: ModelRegistryItem) => {
          const isChampion = model.model_name === activeChampionName

          return (
            <Card
              key={model.model_name}
              className={`relative overflow-hidden transition-all ${
                isChampion
                  ? 'border-amber-500/50 bg-amber-50/20 shadow-md dark:bg-amber-950/10'
                  : 'hover:border-primary/50'
              }`}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-1">
                    <CardTitle className="text-base font-bold flex items-center gap-1.5">
                      {isChampion ? (
                        <Trophy className="text-amber-500" size={18} />
                      ) : (
                        <Swords className="text-blue-500" size={18} />
                      )}
                      {model.algo}
                    </CardTitle>
                    <CardDescription className="text-xs font-mono">
                      {model.model_name}
                    </CardDescription>
                  </div>
                  {isChampion ? (
                    <Badge className="bg-amber-500 text-white hover:bg-amber-600">
                      🏆 Champion
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="text-muted-foreground">
                      Challenger
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-3 text-xs">
                <div className="grid grid-cols-2 gap-2 rounded-md bg-muted/50 p-2.5">
                  <div>
                    <span
                      className="text-muted-foreground cursor-help border-b border-dotted border-muted-foreground/50"
                      title="ROC-AUC (Receiver Operating Characteristic): Mede a capacidade global do modelo de diferenciar clientes que cancelam dos que permanecem (0.5 = chute aleatório, 1.0 = separação perfeita)."
                    >
                      ROC-AUC:
                    </span>
                    <div className="font-mono text-sm font-bold text-foreground">
                      {model.metrics.roc_auc.toFixed(4)}
                    </div>
                  </div>
                  <div>
                    <span
                      className="text-muted-foreground cursor-help border-b border-dotted border-muted-foreground/50"
                      title="PR-AUC (Precision-Recall Area Under Curve): Métrica de ouro para classes desbalanceadas. Mede o percentual de acertos reais de churn minimizando falsos positivos."
                    >
                      PR-AUC:
                    </span>
                    <div className="font-mono text-sm font-bold text-foreground">
                      {model.metrics.pr_auc.toFixed(4)}
                    </div>
                  </div>
                  <div>
                    <span
                      className="text-muted-foreground cursor-help border-b border-dotted border-muted-foreground/50"
                      title="F1-Score: Média harmônica entre Precisão e Recall. Representa o equilíbrio ideal entre não deixar passar clientes em risco e não disparar custos à toa."
                    >
                      F1-Score:
                    </span>
                    <div className="font-mono text-sm font-semibold text-foreground">
                      {model.metrics.f1.toFixed(4)}
                    </div>
                  </div>
                  <div>
                    <span
                      className="text-muted-foreground cursor-help border-b border-dotted border-muted-foreground/50"
                      title="Latência de Inferência: Tempo médio (em milissegundos) que o modelo leva para calcular o score e retornar a predição para a aplicação."
                    >
                      Latência:
                    </span>
                    <div className="font-mono text-sm font-semibold text-foreground">
                      {model.metrics.latency_ms.toFixed(3)} ms
                    </div>
                  </div>
                </div>

                {!isChampion && (
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full gap-1 text-xs"
                    disabled={promoteMutation.isPending}
                    onClick={() => promoteMutation.mutate(model.model_name)}
                  >
                    <ArrowUpRight size={14} />
                    Promover a Champion
                  </Button>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Seção 2: Shadow Scoring Telemetry */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <div>
            <CardTitle className="text-base flex items-center gap-2">
              <Zap className="text-amber-500" size={18} />
              Shadow Scoring em Tempo Real
            </CardTitle>
            <CardDescription className="text-xs">
              Inferência paralela não-bloqueante nos Challengers comparada contra o Champion ativo.
            </CardDescription>
          </div>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => shadowQuery.refetch()}
            disabled={shadowQuery.isFetching}
          >
            <RefreshCw size={14} className={shadowQuery.isFetching ? 'animate-spin' : ''} />
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="rounded-lg border p-3">
              <div className="text-xs text-muted-foreground">Total Shadow Avaliados</div>
              <div className="text-2xl font-bold font-mono">
                {shadowData?.total_shadow_scored ?? 0}
              </div>
            </div>
            <div className="rounded-lg border p-3">
              <div className="text-xs text-muted-foreground">Concordância Média Global</div>
              <div className="text-2xl font-bold font-mono text-emerald-600">
                {shadowData?.avg_concordance_pct?.toFixed(1) ?? '100.0'}%
              </div>
            </div>
            <div className="rounded-lg border p-3">
              <div className="text-xs text-muted-foreground">Champion em Produção</div>
              <div className="text-lg font-bold truncate text-foreground font-mono">
                {activeChampionName}
              </div>
            </div>
          </div>

          {shadowData && shadowData.model_comparisons.length > 0 && (
            <div className="space-y-2">
              <div className="text-xs font-semibold text-muted-foreground">
                Concordância por Modelo Challenger:
              </div>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                {shadowData.model_comparisons.map((comp) => (
                  <div key={comp.model_name} className="rounded-md border p-3 text-xs space-y-1.5">
                    <div className="font-semibold text-foreground truncate">{comp.model_name}</div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Taxa de Acordo:</span>
                      <span className="font-mono font-bold text-emerald-600">
                        {comp.agreement_rate_pct.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Latência Média:</span>
                      <span className="font-mono">{comp.avg_latency_ms.toFixed(3)} ms</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Δ Probabilidade Média:</span>
                      <span className="font-mono">{(comp.avg_prob_diff * 100).toFixed(2)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Seção 3: Tabela Comparativa Completa de Métricas */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Gauge size={18} />
            Matriz Comparativa de Performance
          </CardTitle>
          <CardDescription className="text-xs">
            Métricas extraídas no conjunto de teste independente (1.409 amostras estratificadas).
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b bg-muted/50 text-muted-foreground">
                <tr>
                  <th className="p-2.5 font-medium">Modelo / Algoritmo</th>
                  <th className="p-2.5 font-medium">Papel</th>
                  <th className="p-2.5 font-medium cursor-help" title="ROC-AUC: Capacidade global de discriminação entre churn e não-churn (0.5 a 1.0).">
                    <span className="border-b border-dotted border-muted-foreground/50">ROC-AUC</span>
                  </th>
                  <th className="p-2.5 font-medium cursor-help" title="PR-AUC: Precisão versus Recall para a classe minoritária (Churn).">
                    <span className="border-b border-dotted border-muted-foreground/50">PR-AUC</span>
                  </th>
                  <th className="p-2.5 font-medium cursor-help" title="F1-Score: Média harmônica entre Precisão e Recall.">
                    <span className="border-b border-dotted border-muted-foreground/50">F1-Score</span>
                  </th>
                  <th className="p-2.5 font-medium cursor-help" title="Recall (Sensibilidade): Proporção de cancelamentos reais identificados pelo modelo.">
                    <span className="border-b border-dotted border-muted-foreground/50">Recall</span>
                  </th>
                  <th className="p-2.5 font-medium cursor-help" title="Precision: Proporção de acertos entre todos os clientes previstos como churn.">
                    <span className="border-b border-dotted border-muted-foreground/50">Precision</span>
                  </th>
                  <th className="p-2.5 font-medium cursor-help" title="Brier Score: Calibração de probabilidade (menor é melhor; 0.0 é calibração perfeita).">
                    <span className="border-b border-dotted border-muted-foreground/50">Brier Score</span>
                  </th>
                  <th className="p-2.5 font-medium cursor-help" title="Latência: Tempo médio de resposta por inferência em milissegundos.">
                    <span className="border-b border-dotted border-muted-foreground/50">Latência (ms)</span>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y font-mono">
                {models.map((m) => {
                  const isChamp = m.model_name === activeChampionName
                  return (
                    <tr key={m.model_name} className={isChamp ? 'bg-amber-500/5 font-semibold' : ''}>
                      <td className="p-2.5 font-sans font-medium">
                        {m.algo} <span className="text-xs text-muted-foreground font-mono">({m.model_name})</span>
                      </td>
                      <td className="p-2.5 font-sans">
                        {isChamp ? (
                          <Badge className="bg-amber-500 text-white">🏆 Champion</Badge>
                        ) : (
                          <Badge variant="outline">Challenger</Badge>
                        )}
                      </td>
                      <td className="p-2.5 text-foreground">{m.metrics.roc_auc.toFixed(4)}</td>
                      <td className="p-2.5 text-foreground">{m.metrics.pr_auc.toFixed(4)}</td>
                      <td className="p-2.5 text-foreground">{m.metrics.f1.toFixed(4)}</td>
                      <td className="p-2.5 text-foreground">{m.metrics.recall.toFixed(4)}</td>
                      <td className="p-2.5 text-foreground">{m.metrics.precision.toFixed(4)}</td>
                      <td className="p-2.5 text-foreground">{m.metrics.brier_score.toFixed(4)}</td>
                      <td className="p-2.5 text-foreground">{m.metrics.latency_ms.toFixed(3)}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
