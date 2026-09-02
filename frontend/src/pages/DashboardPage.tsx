import { useMemo } from 'react'
import { Download, FileText } from 'lucide-react'

import { juntarLinhas, type AnalysisResult } from '@/api/queries'
import { AnalysisGate } from '@/components/dashboard/AnalysisGate'
import { KpiCards } from '@/components/dashboard/KpiCards'
import { RiskCharts } from '@/components/dashboard/RiskCharts'
import { LiveEventTicker } from '@/components/streaming/LiveEventTicker'
import { Button } from '@/components/ui/button'
import { useLiveStream } from '@/hooks/useLiveStream'
import type { ResumoBatch } from '@/types'

export function DashboardPage() {
  const handleDownloadDossier = () => {
    window.open('/api/v1/analytics/executive-report/download', '_blank')
  }

  return (
    <AnalysisGate>
      {(resultado) => <DashboardContent resultado={resultado} onDownloadDossier={handleDownloadDossier} />}
    </AnalysisGate>
  )
}

function DashboardContent({
  resultado,
  onDownloadDossier,
}: {
  resultado: AnalysisResult
  onDownloadDossier: () => void
}) {
  const { liveScores } = useLiveStream(true)
  const baseLinhas = useMemo(() => juntarLinhas(resultado), [resultado])

  // Recalcula as linhas com as atualizações de score em tempo real do SSE
  const linhas = useMemo(() => {
    return baseLinhas.map((item) => {
      const cleanId = item.customerId.includes('-') && item.customerId.split('-').length > 2
        ? item.customerId.split('-').slice(1).join('-')
        : item.customerId

      const live = liveScores[item.customerId] || liveScores[cleanId]
      if (!live) return item

      return {
        ...item,
        probabilidade: live.new_risk_score,
        nivel: live.risk_level,
        mrrEmRisco: Number((item.monthlyCharges * live.new_risk_score).toFixed(2)),
      }
    })
  }, [baseLinhas, liveScores])

  // Recalcula dinamicamente os KPIs executivos (MRR em risco, clientes em risco e taxa de risco)
  const dynamicResumo: ResumoBatch = useMemo(() => {
    const totalAnalisado = linhas.length
    const emRiscoLinhas = linhas.filter((l) => l.nivel === 'Alto' || l.nivel === 'Crítico')
    const totalEmRisco = emRiscoLinhas.length
    const mrrTotalEmRisco = emRiscoLinhas.reduce((acc, curr) => acc + curr.mrrEmRisco, 0)

    const porNivel = {
      baixo: linhas.filter((l) => l.nivel === 'Baixo').length,
      medio: linhas.filter((l) => l.nivel === 'Médio').length,
      alto: linhas.filter((l) => l.nivel === 'Alto').length,
      critico: linhas.filter((l) => l.nivel === 'Crítico').length,
    }

    return {
      ...resultado.resposta.resumo,
      total_analisado: totalAnalisado,
      total_em_risco: totalEmRisco,
      mrr_total_em_risco: Number(mrrTotalEmRisco.toFixed(2)),
      distribuicao_risco: porNivel,
    }
  }, [linhas, resultado.resposta.resumo])

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 pb-1 border-b">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Dashboard Executivo de Retenção</h1>
          <p className="text-xs text-muted-foreground">
            Visão consolidada de receita em risco, distribuição de probabilidade e drivers de churn.
          </p>
        </div>
        <Button
          size="sm"
          variant="outline"
          onClick={onDownloadDossier}
          className="gap-2 border-indigo-500/40 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-50 dark:hover:bg-indigo-950/40 text-xs font-semibold shadow-sm"
        >
          <FileText size={14} className="text-indigo-500" />
          Exportar Dossiê Executivo (PDF/HTML)
          <Download size={12} className="opacity-60" />
        </Button>
      </div>

      {/* Live Ingestion & Chaos Studio Ticker */}
      <LiveEventTicker />

      <KpiCards resumo={dynamicResumo} />
      <RiskCharts resumo={dynamicResumo} linhas={linhas} />
      {resultado.resposta.linhas_invalidas.length > 0 && (
        <p className="text-sm text-muted-foreground">
          {resultado.resposta.linhas_invalidas.length} linha(s) inválida(s) ignorada(s) na
          ingestão.
        </p>
      )}
    </div>
  )
}
