import { useMemo } from 'react'
import {
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

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { NIVEIS, NIVEL_CHART_COLOR, formatBrl } from '@/lib/format'
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

  return (
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
  )
}
