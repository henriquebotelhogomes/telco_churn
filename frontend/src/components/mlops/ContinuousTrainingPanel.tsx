import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  Clock,
  Zap,
  ShieldCheck,
  TrendingUp,
  RefreshCw,
} from 'lucide-react'

import { api } from '@/api/client'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { TrainingJobItem } from '@/types'

export function ContinuousTrainingPanel() {
  const queryClient = useQueryClient()
  const [autoPromote, setAutoPromote] = useState(true)
  const [msg, setMsg] = useState<string | null>(null)

  const jobsQuery = useQuery({
    queryKey: ['training-jobs'],
    queryFn: () => api.listTrainingJobs(),
    refetchInterval: (query) => {
      // Faz polling a cada 3s se houver algum job RUNNING
      const hasRunning = query.state.data?.jobs.some((j) => j.status === 'RUNNING')
      return hasRunning ? 3000 : 15000
    },
  })

  const retrainMutation = useMutation({
    mutationFn: () =>
      api.triggerAutoRetrain({
        trigger_type: 'manual_api',
        auto_promote: autoPromote,
      }),
    onSuccess: (data) => {
      setMsg(`Job '${data.job_id}' iniciado em background! O modelo será avaliado no Quality Gate.`)
      queryClient.invalidateQueries({ queryKey: ['training-jobs'] })
      setTimeout(() => setMsg(null), 8000)
    },
  })

  const jobs = jobsQuery.data?.jobs ?? []
  const hasRunning = jobs.some((j) => j.status === 'RUNNING')

  return (
    <Card className="border-indigo-500/30 bg-indigo-50/10 dark:bg-indigo-950/10">
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-1">
            <CardTitle className="text-base flex items-center gap-2">
              <RotateCcw className="text-indigo-500" size={18} />
              Continuous Training (CT) & Self-Healing Pipeline
            </CardTitle>
            <CardDescription className="text-xs">
              Nível 2 de MLOps: retreinamento automatizado multi-modelo, benchmarking e Quality Gate.
            </CardDescription>
          </div>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-1.5 text-xs text-muted-foreground cursor-pointer select-none">
              <input
                type="checkbox"
                checked={autoPromote}
                onChange={(e) => setAutoPromote(e.target.checked)}
                className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              Auto-promover se superar Champion
            </label>
            <Button
              size="sm"
              className="gap-1.5 text-xs bg-indigo-600 hover:bg-indigo-700 text-white"
              disabled={retrainMutation.isPending || hasRunning}
              onClick={() => retrainMutation.mutate()}
            >
              {hasRunning || retrainMutation.isPending ? (
                <>
                  <RefreshCw size={14} className="animate-spin" />
                  Treinando Candidatos…
                </>
              ) : (
                <>
                  <Zap size={14} />
                  Disparar Retreinamento (CT)
                </>
              )}
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {msg && (
          <div className="flex items-center gap-2 rounded-lg bg-indigo-500/15 p-3 text-xs font-medium text-indigo-800 dark:text-indigo-300">
            <CheckCircle2 size={16} />
            {msg}
          </div>
        )}

        {/* Tabela de Histórico de Execuções de CT */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span className="font-semibold text-foreground">Histórico de Execuções de Retreinamento:</span>
            <Button
              size="sm"
              variant="ghost"
              className="h-6 text-xs gap-1"
              onClick={() => jobsQuery.refetch()}
            >
              <RefreshCw size={12} className={jobsQuery.isFetching ? 'animate-spin' : ''} />
              Atualizar
            </Button>
          </div>

          <div className="overflow-x-auto rounded-md border">
            <table className="w-full text-left text-xs">
              <thead className="border-b bg-muted/50 text-muted-foreground font-medium">
                <tr>
                  <th className="p-2.5">Job ID</th>
                  <th className="p-2.5">Gatilho</th>
                  <th className="p-2.5">Status</th>
                  <th className="p-2.5">Melhor Candidato</th>
                  <th className="p-2.5">Champion (Antes ➔ Depois)</th>
                  <th className="p-2.5">Δ PR-AUC</th>
                  <th className="p-2.5">Duração</th>
                  <th className="p-2.5">Executado em</th>
                </tr>
              </thead>
              <tbody className="divide-y font-mono">
                {jobs.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="p-4 text-center text-muted-foreground font-sans">
                      Nenhum pipeline de Continuous Training executado ainda. Clique em "Disparar Retreinamento" para iniciar.
                    </td>
                  </tr>
                ) : (
                  jobs.map((job: TrainingJobItem) => (
                    <tr key={job.job_id} className="hover:bg-muted/30">
                      <td className="p-2.5 font-semibold text-foreground">{job.job_id}</td>
                      <td className="p-2.5 font-sans">
                        <Badge variant="outline" className="text-[10px]">
                          {job.trigger_type}
                        </Badge>
                      </td>
                      <td className="p-2.5 font-sans">
                        {job.status === 'SUCCESS' && (
                          <Badge className="bg-emerald-500 text-white gap-1 text-[10px]">
                            <ShieldCheck size={10} /> Gate Aprovado
                          </Badge>
                        )}
                        {job.status === 'RUNNING' && (
                          <Badge className="bg-amber-500 text-white gap-1 text-[10px] animate-pulse">
                            <Clock size={10} /> Em Execução…
                          </Badge>
                        )}
                        {job.status === 'REJECTED_BY_GATE' && (
                          <Badge variant="secondary" className="gap-1 text-[10px] text-amber-700">
                            <AlertCircle size={10} /> Rejeitado no Gate
                          </Badge>
                        )}
                        {job.status === 'FAILED' && (
                          <Badge variant="destructive" className="gap-1 text-[10px]">
                            Falha
                          </Badge>
                        )}
                      </td>
                      <td className="p-2.5 text-foreground font-sans">
                        {job.best_candidate ?? '—'}
                      </td>
                      <td className="p-2.5 text-muted-foreground">
                        {job.champion_before}{' '}
                        {job.champion_before !== job.champion_after ? (
                          <span className="text-emerald-600 font-bold">➔ {job.champion_after}</span>
                        ) : (
                          '➔ mantido'
                        )}
                      </td>
                      <td className="p-2.5">
                        {job.metric_improvement > 0 ? (
                          <span className="text-emerald-600 font-bold flex items-center gap-0.5">
                            <TrendingUp size={12} />+{(job.metric_improvement * 100).toFixed(2)}%
                          </span>
                        ) : (
                          <span className="text-muted-foreground font-mono">
                            {(job.metric_improvement * 100).toFixed(2)}%
                          </span>
                        )}
                      </td>
                      <td className="p-2.5 text-muted-foreground">{job.duration_seconds.toFixed(2)}s</td>
                      <td className="p-2.5 text-muted-foreground font-sans">
                        {new Date(job.created_at).toLocaleString('pt-BR')}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
