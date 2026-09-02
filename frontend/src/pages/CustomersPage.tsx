import { useMemo, useState } from 'react'

import { AnalysisGate } from '@/components/dashboard/AnalysisGate'
import { Customer360 } from '@/components/customers/Customer360'
import { RiskQueue } from '@/components/customers/RiskQueue'
import { LiveEventTicker } from '@/components/streaming/LiveEventTicker'
import { useLiveStream } from '@/hooks/useLiveStream'
import { juntarLinhas, type AnalysisResult, type LinhaRisco } from '@/api/queries'

export function CustomersPage() {
  return (
    <AnalysisGate>
      {(resultado) => <CustomersContent resultado={resultado} />}
    </AnalysisGate>
  )
}

function CustomersContent({ resultado }: { resultado: AnalysisResult }) {
  const { liveScores } = useLiveStream(true)
  const baseLinhas = useMemo(() => juntarLinhas(resultado), [resultado])

  // Aplica atualizações de risco dinâmicas recebidas via SSE
  const linhas = useMemo(() => {
    return baseLinhas.map((item) => {
      // Extrai o ID puro caso tenha prefixo (ex: TIM-7590-VHVEG -> 7590-VHVEG)
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

  const [selecionada, setSelecionada] = useState<LinhaRisco | null>(null)

  return (
    <div className="space-y-4">
      {/* Ticker de streaming e injeção de caos */}
      <LiveEventTicker />

      <RiskQueue linhas={linhas} onSelect={setSelecionada} />
      <Customer360 linha={selecionada} onClose={() => setSelecionada(null)} />
    </div>
  )
}
