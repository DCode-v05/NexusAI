import { RadialBarChart, RadialBar, ResponsiveContainer, PolarAngleAxis } from 'recharts'

interface RiskGaugeProps {
  score: number
  tier: string
}

const tierColor = (tier: string) => {
  switch (tier?.toLowerCase()) {
    case 'low':      return '#16A34A'
    case 'moderate': return '#D97706'
    case 'high':     return '#EA580C'
    case 'crisis':   return '#DC2626'
    default:         return '#94a3b8'
  }
}

export default function RiskGauge({ score, tier }: RiskGaugeProps) {
  const pct = Math.round(score * 100)
  const color = tierColor(tier)

  return (
    <div className="relative flex items-center justify-center">
      <ResponsiveContainer width={140} height={140}>
        <RadialBarChart
          cx="50%"
          cy="50%"
          innerRadius={45}
          outerRadius={65}
          startAngle={180}
          endAngle={-180}
          data={[{ value: pct, fill: color }]}
        >
          <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
          <RadialBar dataKey="value" cornerRadius={6} background={{ fill: '#f1f5f9' }} />
        </RadialBarChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-slate-800">{pct}</span>
        <span className="text-[10px] font-medium uppercase tracking-wide" style={{ color }}>
          {tier}
        </span>
      </div>
    </div>
  )
}
