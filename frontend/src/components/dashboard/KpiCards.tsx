import { AlertTriangle, DollarSign, HelpCircle, Percent, Users } from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
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
      explicacao:
        'A sigla MRR vem de Monthly Recurring Revenue (Receita Recorrente Mensal). O MRR em Risco representa o montante financeiro mensal esperado em Reais (R$) sob risco de perda imediata.',
      icone: DollarSign,
    },
    {
      titulo: 'Clientes em risco',
      valor: formatInt(resumo.total_em_risco),
      detalhe: 'níveis Alto ou Crítico (p ≥ 0,60)',
      explicacao:
        'Número absoluto de clientes cuja probabilidade de churn é classificada como Alta (≥ 50%) ou Crítica (≥ 70%).',
      icone: AlertTriangle,
    },
    {
      titulo: 'Taxa de risco',
      valor: formatPercent(taxaRisco),
      detalhe: `${formatInt(resumo.total_em_risco)} de ${formatInt(resumo.total_analisado)}`,
      explicacao:
        'Proporção percentual (%) de clientes da base ativa que estão atualmente em zona de risco de cancelamento.',
      icone: Percent,
    },
    {
      titulo: 'Clientes analisados',
      valor: formatInt(resumo.total_analisado),
      detalhe: 'linhas válidas do lote',
      explicacao:
        'Total de clientes da operadora processados e validados pelo pipeline de inferência nesta partição.',
      icone: Users,
    },
  ]

  return (
    <TooltipProvider delayDuration={100}>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {kpis.map(({ titulo, valor, detalhe, explicacao, icone: Icone }) => (
          <Card key={titulo} className="relative group">
            <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
              <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Icone size={16} aria-hidden /> {titulo}
              </CardTitle>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    aria-label={`Mais informações sobre ${titulo}`}
                    className="text-muted-foreground/50 hover:text-foreground transition-colors cursor-help"
                  >
                    <HelpCircle size={14} />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="top" className="max-w-xs text-xs p-2.5 leading-relaxed font-normal">
                  {explicacao}
                </TooltipContent>
              </Tooltip>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-semibold tabular-nums">{valor}</div>
              <p className="text-xs text-muted-foreground">{detalhe}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </TooltipProvider>
  )
}

