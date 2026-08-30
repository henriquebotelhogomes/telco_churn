import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { FlaskConical, Lightbulb, RefreshCw } from 'lucide-react'

import { api } from '@/api/client'
import { RiskGauge } from '@/components/charts/RiskGauge'
import { ShapWaterfall } from '@/components/charts/ShapWaterfall'
import { CopilotRetentionAssistant } from '@/components/customers/CopilotRetentionAssistant'
import { RiskBadge } from '@/components/ui/risk-badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { Skeleton } from '@/components/ui/skeleton'
import { ACAO_LABEL, formatBrl, formatPercent } from '@/lib/format'
import { canonicalToClientePt } from '@/lib/csv'
import type { LinhaRisco } from '@/api/queries'
import type { AcaoSimulavel, ClientePt } from '@/types'

const ACOES: AcaoSimulavel[] = ['fidelizacao', 'protecao', 'autopagamento', 'desconto_15']

interface Customer360Props {
  linha: LinhaRisco | null
  onClose: () => void
}

export function Customer360({ linha, onClose }: Customer360Props) {
  const cliente = useMemo<ClientePt | null>(
    () => (linha ? canonicalToClientePt(linha.row) : null),
    [linha],
  )

  const explicacao = useQuery({
    queryKey: ['predict-360', linha?.indice, linha?.customerId],
    queryFn: () => api.predict(cliente as ClientePt),
    enabled: linha !== null && cliente !== null,
    staleTime: 5 * 60_000,
  })

  const [acoes, setAcoes] = useState<AcaoSimulavel[]>([])
  const [debouncedAcoes, setDebouncedAcoes] = useState<AcaoSimulavel[]>([])
  const [mensagemSucesso, setMensagemSucesso] = useState<string | null>(null)

  useEffect(() => {
    setAcoes([])
    setDebouncedAcoes([])
    setMensagemSucesso(null)
  }, [linha?.indice])

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedAcoes(acoes), 300)
    return () => clearTimeout(timer)
  }, [acoes])

  const historicoQuery = useQuery({
    queryKey: ['playbooks-history', linha?.customerId],
    queryFn: () => api.playbooksHistory(linha?.customerId),
    enabled: !!linha?.customerId,
  })

  const aplicarMutation = useMutation({
    mutationFn: (payload: { playbook: string; desc: string; savings: number; delta: number }) => {
      if (!linha?.customerId) throw new Error('Cliente inválido')
      return api.applyPlaybook({
        customer_id: linha.customerId,
        playbook: payload.playbook,
        description: payload.desc,
        estimated_risk_reduction: Math.abs(payload.delta),
        expected_annual_savings: payload.savings,
        applied_by: 'analyst_current',
      })
    },
    onSuccess: (res) => {
      setMensagemSucesso(res.message)
      historicoQuery.refetch()
    },
  })

  const simulacao = useMutation({
    mutationFn: (selecionadas: AcaoSimulavel[]) =>
      api.simulate(cliente as ClientePt, selecionadas),
  })

  useEffect(() => {
    if (debouncedAcoes.length > 0 && cliente) simulacao.mutate(debouncedAcoes)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedAcoes, cliente])

  const toggleAcao = (acao: AcaoSimulavel) => {
    setAcoes((atuais) =>
      atuais.includes(acao) ? atuais.filter((a) => a !== acao) : [...atuais, acao],
    )
  }

  const dadosSimulacao = simulacao.data

  return (
    <Sheet open={linha !== null} onOpenChange={(aberto) => !aberto && onClose()}>
      <SheetContent side="right" className="w-full overflow-y-auto sm:max-w-xl">
        {linha && (
          <>
            <SheetHeader>
              <SheetTitle className="flex flex-wrap items-center gap-2">
                {linha.customerId} <RiskBadge nivel={linha.nivel} />
              </SheetTitle>
              <SheetDescription>
                Contrato {linha.contract} · {linha.tenure} meses · mensalidade{' '}
                {formatBrl(linha.monthlyCharges)}
              </SheetDescription>
            </SheetHeader>

            <div className="mt-4 space-y-4">
              <Card>
                <CardHeader className="pb-0">
                  <CardTitle className="text-sm font-semibold">Risco de Churn do Cliente</CardTitle>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Probabilidade preditiva calibrada pelo modelo com classificação de severidade
                  </p>
                </CardHeader>
                <CardContent>
                  <RiskGauge probabilidade={linha.probabilidade} nivel={linha.nivel} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-semibold">Top Fatores de Risco (TreeSHAP)</CardTitle>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Impacto marginal de cada atributo na decisão (vermelho eleva o risco, verde reduz)
                  </p>
                </CardHeader>
                <CardContent>
                  {explicacao.isPending && <Skeleton className="h-40" />}
                  {explicacao.isError && (
                    <div className="space-y-2 text-sm text-destructive">
                      Falha ao explicar: {explicacao.error.message}
                      <Button variant="outline" size="sm" onClick={() => explicacao.refetch()}>
                        <RefreshCw aria-hidden /> Tentar novamente
                      </Button>
                    </div>
                  )}
                  {explicacao.data && (
                    <div className="space-y-3">
                      <ShapWaterfall fatores={explicacao.data.top_fatores_risco} />
                      {explicacao.data.acao_recomendada && (
                        <div className="space-y-2 rounded-md bg-muted p-3 text-sm">
                          <div className="flex items-start gap-2">
                            <Lightbulb className="mt-0.5 shrink-0" aria-hidden />
                            <div>
                              <strong>{explicacao.data.acao_recomendada.playbook}</strong> —{' '}
                              {explicacao.data.acao_recomendada.descricao}{' '}
                              <span className="text-muted-foreground">
                                (redução estimada{' '}
                                {formatPercent(explicacao.data.acao_recomendada.reducao_estimada_risco)})
                              </span>
                            </div>
                          </div>
                          <div className="flex justify-end pt-1">
                            <Button
                              size="sm"
                              disabled={aplicarMutation.isPending}
                              onClick={() => {
                                const acao = explicacao.data?.acao_recomendada
                                if (acao) {
                                  aplicarMutation.mutate({
                                    playbook: acao.playbook,
                                    desc: acao.descricao,
                                    savings: linha.monthlyCharges * 12 * acao.reducao_estimada_risco,
                                    delta: -acao.reducao_estimada_risco,
                                  })
                                }
                              }}
                            >
                              Aplicar Playbook Recomendado
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>

              {mensagemSucesso && (
                <div className="rounded-md bg-emerald-500/15 p-3 text-sm text-emerald-800 dark:text-emerald-300">
                  ✅ {mensagemSucesso}
                </div>
              )}

              <CopilotRetentionAssistant
                customerId={linha.customerId}
                cliente={linha.row}
                previsao={explicacao.data}
                playbookSugerido={explicacao.data?.acao_recomendada?.playbook}
                economiaEsperada={
                  explicacao.data?.acao_recomendada
                    ? linha.monthlyCharges *
                      12 *
                      explicacao.data.acao_recomendada.reducao_estimada_risco
                    : 120.0
                }
              />

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-2 text-sm font-semibold">
                    <FlaskConical aria-hidden size={16} /> Simulador Prescritivo What-If
                  </CardTitle>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Simule ações comerciais e avalie a redução estimada de probabilidade e retorno financeiro
                  </p>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex flex-wrap gap-2">
                    {ACOES.map((acao) => (
                      <Button
                        key={acao}
                        size="sm"
                        variant={acoes.includes(acao) ? 'default' : 'outline'}
                        aria-pressed={acoes.includes(acao)}
                        onClick={() => toggleAcao(acao)}
                      >
                        {ACAO_LABEL[acao]}
                      </Button>
                    ))}
                  </div>
                  {acoes.length === 0 && (
                    <p className="text-sm text-muted-foreground">
                      Selecione ações para simular o novo risco e a economia anual esperada.
                    </p>
                  )}
                  {simulacao.isPending && <Skeleton className="h-20" />}
                  {simulacao.isError && (
                    <p className="text-sm text-destructive">{simulacao.error.message}</p>
                  )}
                  {dadosSimulacao && (
                    <ul className="space-y-2">
                      {dadosSimulacao.resultados.map((resultado) => (
                        <li
                          key={resultado.acao}
                          className="space-y-2 rounded-md border p-3 text-sm"
                          data-melhor={dadosSimulacao.melhor_acao === resultado.acao || undefined}
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <span className="font-medium">
                              {ACAO_LABEL[resultado.acao] ?? resultado.acao}
                            </span>
                            <span className="font-mono tabular-nums">
                              {formatPercent(dadosSimulacao.original_probability)} →{' '}
                              {formatPercent(resultado.simulated_probability)}
                            </span>
                          </div>
                          <div className="flex flex-wrap items-center justify-between gap-2 text-muted-foreground">
                            <div className="flex items-center gap-2">
                              <span
                                className={
                                  resultado.delta_risk < 0 ? 'text-emerald-600 font-medium' : 'text-red-600'
                                }
                              >
                                Δ risco {formatPercent(resultado.delta_risk)}
                              </span>
                              <Separator orientation="vertical" className="h-3" />
                              <span>
                                Economia:{' '}
                                <strong className="text-foreground">
                                  {formatBrl(resultado.roi_expected_annual_savings)}
                                </strong>
                              </span>
                            </div>
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={aplicarMutation.isPending}
                              onClick={() => {
                                aplicarMutation.mutate({
                                  playbook: resultado.playbook,
                                  desc: resultado.descricao,
                                  savings: resultado.roi_expected_annual_savings,
                                  delta: resultado.delta_risk,
                                })
                              }}
                            >
                              Aplicar Esta Ação
                            </Button>
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </CardContent>
              </Card>

              {historicoQuery.data && historicoQuery.data.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-semibold">Histórico de Playbooks Aplicados & Fechamento de Ciclo</CardTitle>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      Registro de ações aplicadas, analista responsável e desfecho real observado
                    </p>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2 text-xs">
                      {historicoQuery.data.map((item) => (
                        <li key={item.id} className="flex items-center justify-between border-b pb-1">
                          <div>
                            <span className="font-semibold">{item.playbook}</span> ({item.applied_by})
                          </div>
                          <span className="text-muted-foreground">
                            {new Date(item.created_at).toLocaleDateString('pt-BR')}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  )
}
