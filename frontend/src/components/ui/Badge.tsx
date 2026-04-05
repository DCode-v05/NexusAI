type RiskVariant = 'low' | 'moderate' | 'high' | 'crisis' | 'default'

interface BadgeProps {
  variant?: RiskVariant
  children: React.ReactNode
  className?: string
}

const variantClasses: Record<RiskVariant, string> = {
  low:      'bg-green-50 text-green-700 border border-green-200',
  moderate: 'bg-yellow-50 text-yellow-700 border border-yellow-200',
  high:     'bg-orange-50 text-orange-700 border border-orange-200',
  crisis:   'bg-red-50 text-red-700 border border-red-200',
  default:  'bg-slate-100 text-slate-600 border border-slate-200',
}

export function getRiskVariant(tier: string): RiskVariant {
  const t = tier?.toLowerCase()
  if (t === 'low') return 'low'
  if (t === 'moderate') return 'moderate'
  if (t === 'high') return 'high'
  if (t === 'crisis') return 'crisis'
  return 'default'
}

export default function Badge({ variant = 'default', children, className = '' }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${variantClasses[variant]} ${className}`}
    >
      {children}
    </span>
  )
}
