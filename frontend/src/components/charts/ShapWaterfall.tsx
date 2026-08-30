import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { parseImpact } from '@/lib/format'
import type { FatorRisco } from '@/types'

interface ShapWaterfallProps {
  fatores: FatorRisco[]
}

/** Waterfall SHAP divergente: vermelho aumenta risco (+), verde reduz (−). */
export function ShapWaterfall({ fatores }: ShapWaterfallProps) {
  const data = fatores.map((fator) => ({
    fator: fator.fator,
    impacto: parseImpact(fator.impacto) * 100,
    direcao: fator.direcao,
    descricao: fator.descricao,
    shap_value: fator.shap_value,
  }))

  return (
    <ResponsiveContainer width="100%" height={Math.max(150, data.length * 58)}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 28, top: 4, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis
          type="number"
          tickFormatter={(v: number) => `${v > 0 ? '+' : ''}${v.toFixed(0)}%`}
          tick={{ fontSize: 12 }}
        />
        <YAxis type="category" dataKey="fator" width={150} tick={{ fontSize: 12 }} />
        <ReferenceLine x={0} stroke="var(--color-border)" />
        <Tooltip
          formatter={(valor: any, _nome: any, item: any) => [
            `${Number(valor) > 0 ? '+' : ''}${Number(valor).toFixed(1)}% (SHAP ${item?.payload?.shap_value})`,
            item?.payload?.descricao,
          ]}
        />
        <Bar dataKey="impacto" radius={4} isAnimationActive={false}>
          {data.map((entrada, i) => (
            <Cell key={i} fill={entrada.direcao === 'aumenta_risco' ? '#ef4444' : '#10b981'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
