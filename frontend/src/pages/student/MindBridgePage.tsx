import { useState, useRef } from 'react'
import { useMutation } from '@tanstack/react-query'
import {
  Heart, CloudRain, Focus, Sparkles, Shield,
  AlertTriangle, Activity, Phone,
} from 'lucide-react'
import Button from '../../components/ui/Button'
import ChatPanel, { ChatPanelRef } from '../../components/chat/ChatPanel'
import { wellbeingApi, RiskResult } from '../../api/wellbeing'

/* ------------------------------------------------------------------ */
/*  Tier config                                                        */
/* ------------------------------------------------------------------ */

const tierMeta: Record<string, {
  color: string; bg: string; border: string
  icon: React.ReactNode; label: string; message: string
}> = {
  low: {
    color: '#16A34A', bg: 'bg-green-50', border: 'border-green-200',
    icon: <Shield size={16} className="text-green-600" />,
    label: 'Low Risk',
    message: "You're doing well! Keep taking care of yourself.",
  },
  moderate: {
    color: '#D97706', bg: 'bg-amber-50', border: 'border-amber-200',
    icon: <AlertTriangle size={16} className="text-amber-600" />,
    label: 'Moderate',
    message: 'Consider trying a coping strategy or talking to someone you trust.',
  },
  high: {
    color: '#EA580C', bg: 'bg-orange-50', border: 'border-orange-200',
    icon: <AlertTriangle size={16} className="text-orange-600" />,
    label: 'High Risk',
    message: "Your counselor has been notified. Please don't hesitate to reach out.",
  },
  crisis: {
    color: '#DC2626', bg: 'bg-red-50', border: 'border-red-200',
    icon: <Phone size={16} className="text-red-600" />,
    label: 'Crisis',
    message: 'Please contact iCall now: 9152987821',
  },
}

/* ------------------------------------------------------------------ */
/*  Score Ring                                                         */
/* ------------------------------------------------------------------ */

function ScoreRing({ score, tier }: { score: number; tier: string }) {
  const pct = Math.round(score * 100)
  const r = 52
  const C = 2 * Math.PI * r
  const offset = C - (pct / 100) * C
  const color = tierMeta[tier]?.color ?? '#16A34A'

  return (
    <div className="relative w-[7.5rem] h-[7.5rem] shrink-0">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r={r} fill="none" className="stroke-slate-100 dark:stroke-slate-700" strokeWidth="10" />
        <circle
          cx="60" cy="60" r={r} fill="none"
          stroke={color} strokeWidth="10" strokeLinecap="round"
          strokeDasharray={C} strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 1s cubic-bezier(.4,0,.2,1)' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold text-slate-800 dark:text-slate-100 leading-none">{pct}</span>
        <span className="text-[10px] text-slate-400 uppercase tracking-widest mt-0.5">risk %</span>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Signal Breakdown Bar                                               */
/* ------------------------------------------------------------------ */

function SignalBar({ label, value, color }: { label: string; value: number; color: string }) {
  const pct = Math.round(value * 100)
  return (
    <div className="space-y-1">
      <div className="flex justify-between items-center text-xs">
        <span className="text-slate-500 dark:text-slate-400">{label}</span>
        <span className="font-semibold text-slate-700 dark:text-slate-200 tabular-nums">{pct}%</span>
      </div>
      <div className="h-1.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{
            width: `${Math.max(pct, 2)}%`,
            backgroundColor: color,
            transition: 'width 0.8s cubic-bezier(.4,0,.2,1)',
          }}
        />
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Slider Question                                                    */
/* ------------------------------------------------------------------ */

function SliderQuestion({
  label, value, onChange, icon, isInverse,
}: {
  label: string; value: number; onChange: (v: number) => void
  icon: React.ReactNode; isInverse?: boolean
}) {
  const level = isInverse ? 11 - value : value
  const badgeColor =
    level <= 3 ? 'text-green-700 bg-green-50 ring-green-200' :
    level <= 6 ? 'text-amber-700 bg-amber-50 ring-amber-200' :
                 'text-red-700 bg-red-50 ring-red-200'

  return (
    <div className="group space-y-2">
      <div className="flex items-center gap-2.5">
        <span className="text-[#005A70]/70 group-hover:text-[#005A70] transition-colors">{icon}</span>
        <span className="text-[13px] font-medium text-slate-600 dark:text-slate-300 flex-1 leading-snug">{label}</span>
        <span className={`text-xs font-bold w-7 h-7 rounded-lg flex items-center justify-center ring-1 ${badgeColor} transition-colors`}>
          {value}
        </span>
      </div>
      <input
        type="range" min={1} max={10} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-[6px] rounded-full appearance-none bg-gradient-to-r from-slate-200 to-slate-300 cursor-pointer
          [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4
          [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-[#005A70] [&::-webkit-slider-thumb]:shadow-md
          [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-white
          [&::-webkit-slider-thumb]:hover:scale-110 [&::-webkit-slider-thumb]:transition-transform"
      />
      <div className="flex justify-between text-[10px] text-slate-400 px-0.5">
        <span>Not at all</span>
        <span>Very much</span>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Main Page                                                          */
/* ------------------------------------------------------------------ */

export default function MindBridgePage() {
  const [q1, setQ1] = useState(5)
  const [q2, setQ2] = useState(5)
  const [q3, setQ3] = useState(5)
  const [freeText, setFreeText] = useState('')
  const [lastResult, setLastResult] = useState<RiskResult | null>(null)
  const chatRef = useRef<ChatPanelRef>(null)

  const surveyMutation = useMutation({
    mutationFn: () =>
      wellbeingApi.submitSurvey({ q1_score: q1, q2_score: q2, q3_score: q3, free_text: freeText || undefined }),
    onSuccess: (data) => {
      setLastResult(data)
      const meta = tierMeta[data.tier] ?? tierMeta.low
      const extra =
        data.tier === 'crisis' || data.tier === 'high'
          ? " I've notified your counselor. Please reach out for support."
          : ''
      chatRef.current?.addMessage({
        id: String(Date.now()),
        role: 'ai',
        text: `Thanks for completing your check-in. Your current risk level is **${data.tier}** (score: ${(data.score * 100).toFixed(0)}%). ${meta.message}${extra}`,
        tier: data.tier,
        helpline: data.tier === 'crisis' || data.tier === 'high' ? '9152987821' : undefined,
      })
    },
  })

  const meta = lastResult ? (tierMeta[lastResult.tier] ?? tierMeta.low) : null

  return (
    <div className="grid grid-cols-5 gap-5 h-[calc(100vh-8rem)]">

      {/* LEFT PANEL: CHECK-IN + RESULTS */}
      <div className="col-span-2 flex flex-col gap-4 overflow-y-auto scrollbar-thin pr-1">

        {/* Check-in Card */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-card border border-slate-200 dark:border-slate-700/60 overflow-hidden">
          <div className="bg-gradient-to-r from-[#005A70] to-[#007A8D] px-5 py-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center">
                <Sparkles size={16} className="text-white" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Daily Check-in</h3>
                <p className="text-xs text-white/70">How are you feeling today?</p>
              </div>
            </div>
          </div>

          <div className="p-5 space-y-5">
            <SliderQuestion icon={<Heart size={15} />} label="I've been feeling anxious or worried" value={q1} onChange={setQ1} />
            <SliderQuestion icon={<CloudRain size={15} />} label="I've been feeling low or sad" value={q2} onChange={setQ2} />
            <SliderQuestion icon={<Focus size={15} />} label="I've been able to concentrate on tasks" value={q3} onChange={setQ3} isInverse />

            <textarea
              placeholder="Share what's on your mind... (optional)"
              value={freeText}
              onChange={(e) => setFreeText(e.target.value)}
              rows={3}
              className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-slate-50/50 dark:bg-slate-700/50 px-3.5 py-2.5 text-sm text-slate-700 dark:text-slate-200
                placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-[#005A70]/20 focus:border-[#005A70]
                focus:bg-white dark:focus:bg-slate-700 resize-none transition-all"
            />

            <Button
              variant="primary"
              size="lg"
              loading={surveyMutation.isPending}
              onClick={() => surveyMutation.mutate()}
              className="w-full rounded-xl"
            >
              Submit Check-in
            </Button>
          </div>
        </div>

        {/* Score Results (after submission) */}
        {lastResult && meta && (
          <div
            className="bg-white dark:bg-slate-800 rounded-2xl shadow-card border border-slate-200 dark:border-slate-700/60 overflow-hidden"
            style={{ animation: 'fadeSlideIn 0.5s ease-out' }}
          >
            <div className="px-5 pt-5 pb-3 border-b border-slate-100 dark:border-slate-700/60">
              <div className="flex items-center gap-2">
                <Activity size={15} className="text-[#005A70] dark:text-teal-400" />
                <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">Your Assessment</h3>
              </div>
            </div>

            <div className="p-5">
              <div className="flex items-center gap-5 mb-5">
                <ScoreRing score={lastResult.score} tier={lastResult.tier} />
                <div className="flex-1 space-y-2">
                  <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold ${meta.bg} ${meta.border} border`}>
                    {meta.icon}
                    {meta.label}
                  </div>
                  <p className="text-[13px] text-slate-500 dark:text-slate-400 leading-relaxed">{meta.message}</p>
                </div>
              </div>

              <div className="space-y-3 pt-4 border-t border-slate-100 dark:border-slate-700/60">
                <p className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Signal Breakdown</p>
                <SignalBar label="Anomaly Score (0.50)" value={lastResult.anomaly_score} color="#005A70" />
                <SignalBar label="Sentiment Score (0.35)" value={lastResult.sentiment_score} color="#7C3AED" />
                <SignalBar label="Survey Decline (0.15)" value={lastResult.survey_decline} color="#D97706" />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* RIGHT PANEL: UNIFIED CHAT */}
      <ChatPanel
        ref={chatRef}
        initialMessage="Hi! I'm NexusAI, your wellbeing companion. How are you feeling today? You can also complete the check-in on the left."
        className="col-span-3"
        onRiskUpdate={(score, tier) => {
          setLastResult((prev) => ({
            score,
            tier,
            anomaly_score: prev?.anomaly_score ?? 0,
            sentiment_score: prev?.sentiment_score ?? 0,
            survey_decline: prev?.survey_decline ?? 0,
          }))
        }}
      />

      <style>{`
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  )
}
