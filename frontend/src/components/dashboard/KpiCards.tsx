import { AlertTriangle, DollarSign, Percent, Users } from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatBrl, formatInt, formatPercent } from '@/lib/format'
import type { ResumoBatch } from '@/types'

export function KpiCards({ resumo }: { resumo: ResumoBatch }) {
  const taxaRisco =
    resumo.total_analisado > 0 ? resumo.total_em_risco / resumo.total_analisado : 0

  const kpis = [
    {
      titulo: 'MRR em risco',
      valor: formatBrl(resumo.mrr_total_em_risco),
      detalhe: 'Σ mensalidade × p(churn) em Alto/Crítico',
      icone: DollarSign,
    },
    {
      titulo: 'Clientes em risco',
      valor: formatInt(resumo.total_em_risco),
      detalhe: 'níveis Alto ou Crítico (p ≥ 0,60)',
      icone: AlertTriangle,
    },
    {
      titulo: 'Taxa de risco',
      valor: formatPercent(taxaRisco),
      detalhe: `${formatInt(resumo.total_em_risco)} de ${formatInt(resumo.total_analisado)}`,
      icone: Percent,
    },
    {
      titulo: 'Clientes analisados',
      valor: formatInt(resumo.total_analisado),
      detalhe: 'linhas válidas do lote',
      icone: Users,
    },
  ]

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {kpis.map(({ titulo, valor, detalhe, icone: Icone }) => (
        <Card key={titulo}>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <Icone size={16} aria-hidden /> {titulo}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold tabular-nums">{valor}</div>
            <p className="text-xs text-muted-foreground">{detalhe}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
