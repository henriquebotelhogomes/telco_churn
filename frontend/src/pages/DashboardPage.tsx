import { Download, FileText } from 'lucide-react'

import { juntarLinhas } from '@/api/queries'
import { AnalysisGate } from '@/components/dashboard/AnalysisGate'
import { KpiCards } from '@/components/dashboard/KpiCards'
import { RiskCharts } from '@/components/dashboard/RiskCharts'
import { Button } from '@/components/ui/button'

export function DashboardPage() {
  const handleDownloadDossier = () => {
    window.open('/api/v1/analytics/executive-report/download', '_blank')
  }

  return (
    <AnalysisGate>
      {(resultado) => (
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
              onClick={handleDownloadDossier}
              className="gap-2 border-indigo-500/40 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-50 dark:hover:bg-indigo-950/40 text-xs font-semibold shadow-sm"
            >
              <FileText size={14} className="text-indigo-500" />
              Exportar Dossiê Executivo (PDF/HTML)
              <Download size={12} className="opacity-60" />
            </Button>
          </div>

          <KpiCards resumo={resultado.resposta.resumo} />
          <RiskCharts
            resumo={resultado.resposta.resumo}
            linhas={juntarLinhas(resultado)}
          />
          {resultado.resposta.linhas_invalidas.length > 0 && (
            <p className="text-sm text-muted-foreground">
              {resultado.resposta.linhas_invalidas.length} linha(s) inválida(s) ignorada(s) na
              ingestão.
            </p>
          )}
        </div>
      )}
    </AnalysisGate>
  )
}
