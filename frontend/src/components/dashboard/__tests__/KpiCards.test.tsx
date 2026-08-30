import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'

import { KpiCards } from '@/components/dashboard/KpiCards'
import type { ResumoBatch } from '@/types'

const RESUMO: ResumoBatch = {
  total_analisado: 100,
  total_em_risco: 25,
  mrr_total_em_risco: 1234.56,
  distribuicao_risco: { baixo: 50, medio: 25, alto: 15, critico: 10 },
}

describe('KpiCards', () => {
  it('renderiza os quatro KPIs do resumo batch', () => {
    render(<KpiCards resumo={RESUMO} />)
    expect(screen.getByText('MRR em risco')).toBeInTheDocument()
    expect(screen.getByText('Clientes em risco')).toBeInTheDocument()
    expect(screen.getByText('Taxa de risco')).toBeInTheDocument()
    expect(screen.getByText('Clientes analisados')).toBeInTheDocument()
  })

  it('formata MRR, contagens e taxa de risco', () => {
    render(<KpiCards resumo={RESUMO} />)
    expect(screen.getByText(/1\.234,56/)).toBeInTheDocument()
    expect(screen.getByText('25.0%')).toBeInTheDocument() // 25/100
    expect(screen.getByText('100')).toBeInTheDocument()
  })

  it('não divide por zero quando o lote é vazio', () => {
    render(
      <KpiCards
        resumo={{
          ...RESUMO,
          total_analisado: 0,
          total_em_risco: 0,
          mrr_total_em_risco: 0,
        }}
      />,
    )
    expect(screen.getByText('0.0%')).toBeInTheDocument()
  })
})
