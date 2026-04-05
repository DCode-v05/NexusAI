import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Clock, TrendingUp, BookOpen, MessageSquare, Flame,
  AlertTriangle, BarChart2, Activity, Brain,
} from 'lucide-react'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge, { getRiskVariant } from '../../components/ui/Badge'
import MoodHistoryChart from '../../components/charts/MoodHistoryChart'
import RiskGauge from '../../components/charts/RiskGauge'
import Spinner from '../../components/ui/Spinner'
import { studentsApi } from '../../api/students'

const signalConfig = [
  { key: 'session_gap_days',      label: 'Session Gap',        icon: <Clock size={16} />,         unit: 'd' },
  { key: 'survey_skip_streak',    label: 'Survey Skips',       icon: <AlertTriangle size={16} />, unit: '' },
  { key: 'avg_session_length',    label: 'Avg Session',        icon: <BarChart2 size={16} />,     unit: 'min' },
  { key: 'assignment_delay_hrs',  label: 'Submit Delay',       icon: <BookOpen size={16} />,      unit: 'h' },
  { key: 'chat_initiation_freq',  label: 'Chat Frequency',     icon: <MessageSquare size={16} />, unit: '/wk' },
  { key: 'mood_score_trend',      label: 'Mood Trend',         icon: <TrendingUp size={16} />,    unit: '' },
  { key: 'login_hour_variance',   label: 'Login Variance',     icon: <Activity size={16} />,      unit: 'h' },
]

// Demo mood: days 1-10 HIGH (7-9), days 11-20 LOW (1.5-3.5), days 21-30 MID (4.5-6.5)
const demoMood = Array.from({ length: 30 }, (_, i) => {
  const jitter = Math.sin(i * 2.3) * 0.8 + Math.cos(i * 1.7) * 0.5
  let val: number
  if (i < 10) {
    // First 10 days: HIGH mood (7-9 range with spikes)
    val = 8 + jitter
  } else if (i < 20) {
    // Next 10 days: LOW mood (1.5-3.5 range, sudden drop)
    val = 2.5 + jitter
  } else {
    // Last 10 days: MID mood (4.5-6.5 range, recovering)
    val = 5.5 + jitter
  }
  return {
    date: new Date(Date.now() - (29 - i) * 86400000).toISOString().split('T')[0],
    composite: Math.round(Math.max(1, Math.min(10, val)) * 10) / 10,
  }
})

const demoBehavior = {
  session_gap_days: 1.2,
  survey_skip_streak: 0,
  avg_session_length: 38.5,
  assignment_delay_hrs: 4.2,
  chat_initiation_freq: 2.8,
  mood_score_trend: 0.3,
  login_hour_variance: 1.8,
}

export default function DashboardPage() {
  const navigate = useNavigate()
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: studentsApi.getDashboard,
    retry: 1,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" />
      </div>
    )
  }

  // API returns MoodSurveyResponse with submitted_at/composite_score — map to date/composite
  const moodData = data?.mood_history?.length
    ? data.mood_history.map((m: any) => ({
        date: m.date ?? m.submitted_at?.split('T')[0] ?? '',
        composite: m.composite ?? m.composite_score ?? 5,
      }))
    : demoMood
  const riskTier = data?.risk_tier ?? 'low'
  const behavior = data?.behavior ?? demoBehavior
  const streakDays = data?.streak_days ?? 3

  return (
    <div className="space-y-6">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-100">
            Welcome back{data?.name ? `, ${data.name}` : ''}
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">Here's your wellbeing overview</p>
        </div>
        {/* ONE primary button */}
        <Button
          variant="primary"
          icon={<Brain size={16} />}
          onClick={() => navigate('/mindbridge')}
        >
          Talk to NexusAI
        </Button>
      </div>

      {/* Top row: Streak + Risk */}
      <div className="grid grid-cols-3 gap-4">
        {/* Streak */}
        <Card className="col-span-1">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-xl bg-orange-50 flex items-center justify-center">
              <Flame size={22} className="text-orange-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-800 dark:text-slate-100">{streakDays}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">Day Streak</p>
            </div>
          </div>
        </Card>

        {/* Risk gauge */}
        <Card className="col-span-1 flex flex-col items-center py-4">
          <p className="text-xs text-slate-500 dark:text-slate-400 font-medium mb-2 uppercase tracking-wide">Risk Level</p>
          <RiskGauge score={0.3} tier={riskTier} />
        </Card>

        {/* Risk badge card */}
        <Card className="col-span-1">
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-2 font-medium">Current Status</p>
          <Badge variant={getRiskVariant(riskTier)} className="text-sm px-3 py-1">
            {riskTier.charAt(0).toUpperCase() + riskTier.slice(1)} Risk
          </Badge>
          <p className="text-xs text-slate-400 mt-3 leading-relaxed">
            Your wellbeing signals are being monitored to support you proactively.
          </p>
        </Card>
      </div>

      {/* Behavioral signals */}
      <Card title="Behavioral Signals" subtitle="Last 7 days">
        <div className="grid grid-cols-7 gap-3">
          {signalConfig.map((sig) => {
            const val = behavior ? (behavior as unknown as Record<string, number>)[sig.key] : null
            return (
              <div
                key={sig.key}
                className="flex flex-col items-center text-center gap-1.5 p-3 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-700/60"
              >
                <span className="text-[#005A70]">{sig.icon}</span>
                <p className="text-xs font-medium text-slate-700 dark:text-slate-200 leading-tight">{sig.label}</p>
                <p className="text-sm font-bold text-slate-800 dark:text-slate-100">
                  {val !== null && val !== undefined ? `${Number(val).toFixed(1)}${sig.unit}` : '—'}
                </p>
              </div>
            )
          })}
        </div>
      </Card>

      {/* Mood chart */}
      <Card title="Mood History" subtitle="30-day trend">
        <MoodHistoryChart data={moodData} />
      </Card>
    </div>
  )
}
