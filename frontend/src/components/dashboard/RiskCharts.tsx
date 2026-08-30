import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { TrendingUp, Award, DollarSign } from 'lucide-react'

import { api } from '@/api/client'
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
          <CardHeader>
            <CardTitle className="text-base">Distribuição de risco</CardTitle>
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
          <CardHeader>
            <CardTitle className="text-base">MRR esperado por nível de risco</CardTitle>
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
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <TrendingUp size={18} /> Evolução Temporal de Churn & Ações de Retenção
            </CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={dadosTemporal} margin={{ left: 8, right: 8, top: 10, bottom: 4 }}>
                <defs>
                  <linearGradient id="corAnalisado" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="corRetidos" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.5} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="periodo" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip
                  formatter={(val: any, nome: any) => [
                    val,
                    nome === 'total_analisado' ? 'Clientes Analisados' : 'Retenções Confirmadas',
                  ]}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="total_analisado"
                  name="Clientes Analisados"
                  stroke="#3b82f6"
                  fillOpacity={1}
                  fill="url(#corAnalisado)"
                />
                <Area
                  type="monotone"
                  dataKey="total_retidos_confirmados"
                  name="Retenções Confirmadas"
                  stroke="#10b981"
                  fillOpacity={1}
                  fill="url(#corRetidos)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
