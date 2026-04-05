import { ButtonHTMLAttributes, ReactNode } from 'react'
import Spinner from './Spinner'

type Variant = 'primary' | 'secondary' | 'ghost' | 'destructive'
type Size = 'sm' | 'md' | 'lg'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  loading?: boolean
  icon?: ReactNode
  children: ReactNode
}

const variantClasses: Record<Variant, string> = {
  primary:
    'bg-[#005A70] text-white hover:bg-[#004557] focus:ring-2 focus:ring-[#005A70]/40 shadow-sm',
  secondary:
    'border border-[#005A70] text-[#005A70] dark:text-teal-300 dark:border-teal-400 hover:bg-[#005A70]/10 focus:ring-2 focus:ring-[#005A70]/30',
  ghost:
    'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 focus:ring-2 focus:ring-slate-300',
  destructive:
    'bg-error text-white hover:bg-red-700 focus:ring-2 focus:ring-red-400/40 shadow-sm',
}

const sizeClasses: Record<Size, string> = {
  sm:  'px-3 py-1.5 text-sm rounded-md gap-1.5',
  md:  'px-6 py-2.5 text-sm rounded-lg gap-2',
  lg:  'px-8 py-3 text-base rounded-xl gap-2.5',
}

export default function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  children,
  disabled,
  className = '',
  ...props
}: ButtonProps) {
  const isDisabled = disabled || loading

  return (
    <button
      disabled={isDisabled}
      className={`
        inline-flex items-center justify-center font-medium transition-all duration-150
        focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${className}
      `}
      {...props}
    >
      {loading ? (
        <Spinner size="sm" className="text-current" />
      ) : icon ? (
        <span className="shrink-0">{icon}</span>
      ) : null}
      {children}
    </button>
  )
}
