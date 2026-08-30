import { useMemo, useState } from 'react'

import { AnalysisGate } from '@/components/dashboard/AnalysisGate'
import { Customer360 } from '@/components/customers/Customer360'
import { RiskQueue } from '@/components/customers/RiskQueue'
import { juntarLinhas, type AnalysisResult, type LinhaRisco } from '@/api/queries'

export function CustomersPage() {
  return (
    <AnalysisGate>
      {(resultado) => <CustomersContent resultado={resultado} />}
    </AnalysisGate>
  )
}

function CustomersContent({ resultado }: { resultado: AnalysisResult }) {
  const linhas = useMemo(() => juntarLinhas(resultado), [resultado])
  const [selecionada, setSelecionada] = useState<LinhaRisco | null>(null)

  return (
    <>
      <RiskQueue linhas={linhas} onSelect={setSelecionada} />
      <Customer360 linha={selecionada} onClose={() => setSelecionada(null)} />
    </>
  )
}
