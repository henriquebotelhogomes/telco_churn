import { Cell, Pie, PieChart, ResponsiveContainer } from 'recharts'

import { NIVEL_CHART_COLOR } from '@/lib/format'

interface RiskGaugeProps {
  probabilidade: number
  nivel: string
}

/** Gauge semicircular (0-100%) colorido pelo nível de risco. */
export function RiskGauge({ probabilidade, nivel }: RiskGaugeProps) {
  const pct = Math.round(probabilidade * 100)
  const data = [
    { name: 'risco', value: pct },
    { name: 'restante', value: Math.max(0, 100 - pct) },
  ]

  return (
    <div className="relative h-28" role="img" aria-label={`Risco de churn: ${pct}%`}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            startAngle={180}
            endAngle={0}
            innerRadius="72%"
            outerRadius="100%"
            stroke="none"
            isAnimationActive={false}
            cy="100%"
          >
            <Cell fill={NIVEL_CHART_COLOR[nivel] ?? '#94a3b8'} />
            <Cell fill="var(--color-muted)" />
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div className="absolute inset-x-0 bottom-0 text-center">
        <span className="text-2xl font-semibold tabular-nums">{pct}%</span>
      </div>
    </div>
  )
}
