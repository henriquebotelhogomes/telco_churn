import { describe, expect, it } from 'vitest'

import { formatBrl, formatInt, formatPercent, parseImpact } from '@/lib/format'

describe('formatBrl', () => {
  it('formata valores monetários em BRL', () => {
    expect(formatBrl(1234.5)).toMatch(/1\.234,50/)
  })
})

describe('formatPercent', () => {
  it('converte fração em porcentagem', () => {
    expect(formatPercent(0.4256)).toBe('42.6%')
  })

  it('respeita casas decimais', () => {
    expect(formatPercent(0.4256, 0)).toBe('43%')
  })
})

describe('formatInt', () => {
  it('usa separador de milhar pt-BR', () => {
    expect(formatInt(7043)).toBe('7.043')
  })
})

describe('parseImpact', () => {
  it('converte impacto positivo', () => {
    expect(parseImpact('+28%')).toBeCloseTo(0.28)
  })

  it('converte impacto negativo', () => {
    expect(parseImpact('-12%')).toBeCloseTo(-0.12)
  })

  it('retorna 0 para entrada inválida', () => {
    expect(parseImpact('abc')).toBe(0)
  })
})
