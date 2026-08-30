import { AnalysisGate } from '@/components/dashboard/AnalysisGate'
import { KpiCards } from '@/components/dashboard/KpiCards'
import { RiskCharts } from '@/components/dashboard/RiskCharts'
import { juntarLinhas } from '@/api/queries'

export function DashboardPage() {
  return (
    <AnalysisGate>
      {(resultado) => (
        <div className="space-y-4">
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
