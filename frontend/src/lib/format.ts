// Formatadores e helpers de apresentação (puro — testável sem DOM).

const brl = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  maximumFractionDigits: 2,
})

export function formatBrl(valor: number): string {
  return brl.format(valor)
}

export function formatPercent(valor: number, digits = 1): string {
  return `${(valor * 100).toFixed(digits)}%`
}

export function formatInt(valor: number): string {
  return new Intl.NumberFormat('pt-BR').format(valor)
}

/** Converte impacto SHAP no formato da API ("+28%", "-12%") em número (0.28, -0.12). */
export function parseImpact(impacto: string): number {
  const limpo = impacto.replace('%', '').replace('+', '').trim()
  const valor = Number(limpo)
  return Number.isFinite(valor) ? valor / 100 : 0
}

export const NIVEIS = ['Baixo', 'Médio', 'Alto', 'Crítico'] as const

export const NIVEL_BADGE_CLASS: Record<string, string> = {
  Baixo: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-400',
  Médio: 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-400',
  Alto: 'bg-orange-100 text-orange-800 dark:bg-orange-500/15 dark:text-orange-400',
  Crítico: 'bg-red-100 text-red-800 dark:bg-red-500/15 dark:text-red-400',
}

export const NIVEL_CHART_COLOR: Record<string, string> = {
  Baixo: '#10b981',
  Médio: '#f59e0b',
  Alto: '#f97316',
  Crítico: '#ef4444',
}

export const ACAO_LABEL: Record<string, string> = {
  fidelizacao: 'Fidelização (contrato 2 anos)',
  protecao: 'Proteção (suporte + segurança)',
  autopagamento: 'Autopagamento (cartão automático)',
  desconto_15: 'Desconto de 15%',
}
