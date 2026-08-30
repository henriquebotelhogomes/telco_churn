import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { TrendingUp, Award, DollarSign, Percent, HelpCircle } from 'lucide-react'

import { api } from '@/api/client'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { NIVEIS, NIVEL_CHART_COLOR, formatBrl, formatPercent } from '@/lib/format'
import type { LinhaRisco } from '@/api/queries'
import type { ResumoBatch } from '@/types'

interface RiskChartsProps {
  resumo: ResumoBatch
  linhas: LinhaRisco[]
}

export function RiskCharts({ resumo, linhas }: RiskChartsProps) {
  const distribuicao = useMemo(
    () => [
      { nivel: 'Baixo', total: resumo.distribuicao_risco.baixo },
      { nivel: 'Médio', total: resumo.distribuicao_risco.medio },
      { nivel: 'Alto', total: resumo.distribuicao_risco.alto },
      { nivel: 'Crítico', total: resumo.distribuicao_risco.critico },
    ],
    [resumo],
  )

  // MRR esperado por nível = Σ(mensalidade × p(churn)) de todas as linhas do nível
  const mrrPorNivel = useMemo(() => {
    const soma = new Map<string, number>(NIVEIS.map((nivel) => [nivel, 0]))
    for (const linha of linhas) {
      soma.set(linha.nivel, (soma.get(linha.nivel) ?? 0) + linha.monthlyCharges * linha.probabilidade)
    }
    return NIVEIS.map((nivel) => ({ nivel, mrr: soma.get(nivel) ?? 0 }))
  }, [linhas])

  const temporalQuery = useQuery({
    queryKey: ['analytics-temporal-evolution'],
    queryFn: () => api.temporalEvolution(),
    staleTime: 60_000,
  })

  const eficienciaQuery = useQuery({
    queryKey: ['analytics-retention-efficiency'],
    queryFn: () => api.retentionEfficiency(),
    staleTime: 60_000,
  })

  const dadosTemporal = temporalQuery.data?.pontos ?? []
  const dadosEficiencia = eficienciaQuery.data

  return (
    <div className="space-y-4">
      {dadosEficiencia && dadosEficiencia.total_acoes_registradas > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Card className="border-emerald-500/30 bg-emerald-50/30 dark:bg-emerald-950/10">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-xs font-medium text-emerald-800 dark:text-emerald-300">
                <Award size={16} /> Eficiência Real de Retenção
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-emerald-700 dark:text-emerald-400">
                {formatPercent(dadosEficiencia.taxa_global_eficiencia_pct / 100)}
              </div>
              <p className="text-xs text-muted-foreground">
                {dadosEficiencia.total_clientes_salvos} de {dadosEficiencia.total_acoes_registradas} clientes retidos
              </p>
            </CardContent>
          </Card>

          <Card className="border-blue-500/30 bg-blue-50/30 dark:bg-blue-950/10">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-xs font-medium text-blue-800 dark:text-blue-300">
                <DollarSign size={16} /> MRR Histórico Preservado
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-700 dark:text-blue-400">
                {formatBrl(dadosEficiencia.mrr_acumulado_salvo)}
              </div>
              <p className="text-xs text-muted-foreground">
                Receita anual salva via playbooks
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                <TrendingUp size={16} /> Playbooks Ativos
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {dadosEficiencia.detalhe_por_playbook.length}
              </div>
              <p className="text-xs text-muted-foreground">
                Estratégias de retenção catalogadas
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Distribuição de Risco</CardTitle>
              <span
                className="text-muted-foreground hover:text-foreground cursor-help p-1"
                title="Contagem absoluta e proporção de clientes categorizados nos 4 níveis de risco de churn: Baixo (<30%), Médio (30-60%), Alto (60-80%) e Crítico (>=80%)."
              >
                <HelpCircle size={15} />
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Proporção e volume de clientes categorizados nos 4 níveis de criticidade
            </p>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={distribuicao}
                  dataKey="total"
                  nameKey="nivel"
                  innerRadius="60%"
                  isAnimationActive={false}
                >
                  {distribuicao.map((entrada) => (
                    <Cell key={entrada.nivel} fill={NIVEL_CHART_COLOR[entrada.nivel]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">MRR Esperado por Nível de Risco</CardTitle>
              <span
                className="text-muted-foreground hover:text-foreground cursor-help p-1"
                title="MRR (Monthly Recurring Revenue / Receita Recorrente Mensal): É a soma da mensalidade de cada cliente multiplicada pela sua probabilidade calculada de cancelamento (Mensalidade × p(Churn)), agrupada por faixa de risco."
              >
                <HelpCircle size={15} />
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Receita Recorrente Mensal ponderada pela probabilidade de cancelamento de cada cliente
            </p>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={mrrPorNivel} margin={{ left: 8, right: 8, top: 4, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="nivel" tick={{ fontSize: 12 }} />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickFormatter={(v: number) => `${Math.round(v / 1000)}k`}
                />
                <Tooltip formatter={(valor: any) => formatBrl(Number(valor))} />
                <Bar dataKey="mrr" name="MRR esperado" radius={[4, 4, 0, 0]} isAnimationActive={false}>
                  {mrrPorNivel.map((entrada) => (
                    <Cell key={entrada.nivel} fill={NIVEL_CHART_COLOR[entrada.nivel]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {dadosTemporal.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <CardTitle className="flex items-center gap-2 text-base">
                  <TrendingUp size={18} className="text-indigo-500" /> Evolução Temporal de Churn & Ações de Retenção
                </CardTitle>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Volume histórico de clientes analisados, retenções confirmadas e taxa de eficácia percentual (%)
                </p>
              </div>
              {temporalQuery.data?.resumo_global && (
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline" className="text-[11px] border-blue-500/30 text-blue-700 dark:text-blue-300">
                    Analisados: {temporalQuery.data.resumo_global.total_analisado.toLocaleString('pt-BR')}
                  </Badge>
                  <Badge variant="outline" className="text-[11px] border-emerald-500/30 text-emerald-700 dark:text-emerald-300">
                    Retidos: {temporalQuery.data.resumo_global.total_retidos.toLocaleString('pt-BR')}
                  </Badge>
                  <Badge className="bg-purple-600 hover:bg-purple-700 text-white text-[11px] font-semibold gap-1">
                    <Percent size={11} />
                    Taxa Global: {temporalQuery.data.resumo_global.taxa_global_retencao_pct}%
                  </Badge>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={dadosTemporal} margin={{ left: 8, right: 12, top: 12, bottom: 4 }}>
                <defs>
                  <linearGradient id="corAnalisado" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="corRetidos" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.45} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="periodo" tick={{ fontSize: 12 }} />
                {/* Eixo Y Esquerdo: Volumes Absolutos */}
                <YAxis
                  yAxisId="left"
                  tick={{ fontSize: 12 }}
                  tickFormatter={(v: number) => (v >= 1000 ? `${(v / 1000).toFixed(1)}k` : `${v}`)}
                />
                {/* Eixo Y Direito: Taxa Percentual (%) */}
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  domain={[0, 100]}
                  tick={{ fontSize: 12, fill: '#8b5cf6' }}
                  tickFormatter={(v: number) => `${v}%`}
                />
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      const d = payload[0].payload
                      return (
                        <div className="rounded-lg border bg-background/95 p-3 shadow-lg backdrop-blur-sm text-xs space-y-1.5 min-w-[210px]">
                          <p className="font-semibold text-foreground border-b pb-1">
                            Período: <span className="font-mono text-indigo-600 dark:text-indigo-400">{label}</span>
                          </p>
                          <div className="flex items-center justify-between gap-3 text-blue-600 dark:text-blue-400">
                            <span>🔵 Clientes Analisados:</span>
                            <span className="font-bold font-mono">{d.total_analisado?.toLocaleString('pt-BR')}</span>
                          </div>
                          <div className="flex items-center justify-between gap-3 text-emerald-600 dark:text-emerald-400">
                            <span>🟢 Retenções Confirmadas:</span>
                            <span className="font-bold font-mono">{d.total_retidos_confirmados?.toLocaleString('pt-BR')}</span>
                          </div>
                          <div className="flex items-center justify-between gap-3 text-purple-600 dark:text-purple-400 font-semibold border-t pt-1">
                            <span>🟣 Taxa de Retenção:</span>
                            <span className="font-bold font-mono">{d.taxa_retencao_pct}%</span>
                          </div>
                          {d.mrr_preservado > 0 && (
                            <div className="flex items-center justify-between gap-3 text-emerald-700 dark:text-emerald-300 text-[11px]">
                              <span>💰 MRR Salvo:</span>
                              <span className="font-mono font-bold">{formatBrl(d.mrr_preservado)}</span>
                            </div>
                          )}
                        </div>
                      )
                    }
                    return null
                  }}
                />
                <Legend verticalAlign="bottom" height={36} />
                <Area
                  yAxisId="left"
                  type="monotone"
                  dataKey="total_analisado"
                  name="Clientes Analisados"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#corAnalisado)"
                />
                <Area
                  yAxisId="left"
                  type="monotone"
                  dataKey="total_retidos_confirmados"
                  name="Retenções Confirmadas"
                  stroke="#10b981"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#corRetidos)"
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="taxa_retencao_pct"
                  name="Taxa de Retenção (%)"
                  stroke="#8b5cf6"
                  strokeWidth={2.5}
                  dot={{ r: 4, fill: '#8b5cf6' }}
                  activeDot={{ r: 6 }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
