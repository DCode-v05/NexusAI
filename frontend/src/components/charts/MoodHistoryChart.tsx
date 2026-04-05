import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Area, AreaChart,
} from 'recharts'

interface MoodEntry {
  date: string
  composite: number
}

interface MoodHistoryChartProps {
  data: MoodEntry[]
}

export default function MoodHistoryChart({ data }: MoodHistoryChartProps) {
  const formatted = data.map((d) => ({
    ...d,
    label: new Date(d.date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }),
  }))

  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={formatted} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="moodGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#005A70" stopOpacity={0.15} />
            <stop offset="95%" stopColor="#005A70" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 11, fill: '#94a3b8' }}
          axisLine={false}
          tickLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          domain={[0, 10]}
          tick={{ fontSize: 11, fill: '#94a3b8' }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{
            background: 'white',
            border: '1px solid #e2e8f0',
            borderRadius: 8,
            fontSize: 12,
          }}
          formatter={(v: number) => [v.toFixed(1), 'Mood']}
        />
        <Area
          type="monotone"
          dataKey="composite"
          stroke="#005A70"
          strokeWidth={2}
          fill="url(#moodGrad)"
          dot={false}
          activeDot={{ r: 4, fill: '#005A70' }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
