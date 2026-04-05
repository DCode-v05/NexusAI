import { ReactNode } from 'react'

interface CardProps {
  title?: string
  subtitle?: string
  footer?: ReactNode
  children: ReactNode
  className?: string
  noPadding?: boolean
}

export default function Card({ title, subtitle, footer, children, className = '', noPadding }: CardProps) {
  return (
    <div className={`bg-white dark:bg-slate-800 rounded-xl shadow-card border border-slate-200 dark:border-slate-700/60 ${className}`}>
      {(title || subtitle) && (
        <div className="px-6 pt-5 pb-4 border-b border-slate-100 dark:border-slate-700/60">
          {title && <h3 className="font-semibold text-slate-800 dark:text-slate-100 text-base">{title}</h3>}
          {subtitle && <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">{subtitle}</p>}
        </div>
      )}
      <div className={noPadding ? '' : 'p-6'}>{children}</div>
      {footer && (
        <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-700/60 bg-slate-50/50 dark:bg-slate-800/50 rounded-b-xl">
          {footer}
        </div>
      )}
    </div>
  )
}
