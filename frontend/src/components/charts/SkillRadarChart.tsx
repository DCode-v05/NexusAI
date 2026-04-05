import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer, Legend,
} from 'recharts'

interface SkillEntry {
  skill: string
  current: number
  required: number
}

interface SkillRadarChartProps {
  data: SkillEntry[]
}

export default function SkillRadarChart({ data }: SkillRadarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <RadarChart data={data}>
        <PolarGrid stroke="#e2e8f0" />
        <PolarAngleAxis dataKey="skill" tick={{ fontSize: 11, fill: '#64748b' }} />
        <Radar
          name="Required"
          dataKey="required"
          stroke="#cbd5e1"
          fill="#cbd5e1"
          fillOpacity={0.3}
        />
        <Radar
          name="Current"
          dataKey="current"
          stroke="#005A70"
          fill="#005A70"
          fillOpacity={0.4}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          formatter={(v) => <span className="text-xs text-slate-600">{v}</span>}
        />
      </RadarChart>
    </ResponsiveContainer>
  )
}
