import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { FlaskConical, Lightbulb, RefreshCw } from 'lucide-react'

import { api } from '@/api/client'
import { RiskGauge } from '@/components/charts/RiskGauge'
import { ShapWaterfall } from '@/components/charts/ShapWaterfall'
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

  useEffect(() => {
    setAcoes([])
    setDebouncedAcoes([])
  }, [linha?.indice])

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedAcoes(acoes), 300)
    return () => clearTimeout(timer)
  }, [acoes])

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
                  <CardTitle className="text-sm text-muted-foreground">Risco de churn</CardTitle>
                </CardHeader>
                <CardContent>
                  <RiskGauge probabilidade={linha.probabilidade} nivel={linha.nivel} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Top fatores de risco (SHAP)</CardTitle>
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
                        <div className="flex items-start gap-2 rounded-md bg-muted p-3 text-sm">
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
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-sm">
                    <FlaskConical aria-hidden /> Simulador What-If
                  </CardTitle>
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
                          className="rounded-md border p-3 text-sm"
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
                          <div className="mt-1 flex flex-wrap items-center gap-3 text-muted-foreground">
                            <span
                              className={
                                resultado.delta_risk < 0 ? 'text-emerald-600' : 'text-red-600'
                              }
                            >
                              Δ risco {formatPercent(resultado.delta_risk)}
                            </span>
                            <Separator orientation="vertical" className="h-3" />
                            <span>
                              Economia anual esperada:{' '}
                              <strong className="text-foreground">
                                {formatBrl(resultado.roi_expected_annual_savings)}
                              </strong>
                            </span>
                            {dadosSimulacao.melhor_acao === resultado.acao && (
                              <RiskBadge nivel="Baixo" />
                            )}
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </CardContent>
              </Card>
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  )
}
