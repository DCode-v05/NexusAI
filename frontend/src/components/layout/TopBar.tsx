import { useState, useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import { Bell, Sun, Moon, X } from 'lucide-react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../../store/authStore'
import { useThemeStore } from '../../store/themeStore'
import { counselorApi, NotificationItem } from '../../api/counselor'

const titles: Record<string, string> = {
  '/dashboard':  'Dashboard',
  '/mindbridge': 'MindBridge',
  '/pathway':    'PathwayAI',
  '/counselor':  'Counselor Dashboard',
}

export default function TopBar() {
  const location = useLocation()
  const user = useAuthStore((s) => s.user)
  const { theme, toggleTheme } = useThemeStore()
  const title = titles[location.pathname] ?? 'NexusAI'
  const isDark = theme === 'dark'
  const isStudent = user?.role === 'student'

  const [showNotifs, setShowNotifs] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const qc = useQueryClient()

  // Fetch notifications for students
  const { data: notifications = [] } = useQuery({
    queryKey: ['notifications'],
    queryFn: counselorApi.getNotifications,
    enabled: isStudent,
    refetchInterval: 15_000,
  })

  const unreadCount = notifications.filter((n) => !n.is_read).length

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowNotifs(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleBellClick = async () => {
    setShowNotifs(!showNotifs)
    if (!showNotifs && unreadCount > 0) {
      await counselorApi.markNotificationsRead()
      qc.invalidateQueries({ queryKey: ['notifications'] })
    }
  }

  return (
    <header className="h-14 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700/60 flex items-center justify-between px-6 shrink-0">
      <h1 className="font-semibold text-slate-800 dark:text-slate-100 text-base">{title}</h1>
      <div className="flex items-center gap-3">
        {/* Dark / Light toggle */}
        <button
          onClick={toggleTheme}
          className="relative w-14 h-7 rounded-full transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-[#005A70]/40"
          style={{ backgroundColor: isDark ? '#005A70' : '#E2E8F0' }}
          title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          <span
            className="absolute top-0.5 flex items-center justify-center w-6 h-6 rounded-full bg-white shadow-md transition-transform duration-300"
            style={{ transform: isDark ? 'translateX(30px)' : 'translateX(2px)' }}
          >
            {isDark ? (
              <Moon size={13} className="text-[#005A70]" />
            ) : (
              <Sun size={13} className="text-amber-500" />
            )}
          </span>
        </button>

        {/* Notification bell */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={handleBellClick}
            className="relative text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
          >
            <Bell size={18} />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-500 text-white text-[9px] font-bold flex items-center justify-center">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>

          {/* Notification dropdown */}
          {showNotifs && (
            <div className="absolute right-0 top-10 w-80 bg-white dark:bg-slate-800 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700 z-50 overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-700/60 flex items-center justify-between">
                <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-100">Notifications</h4>
                <button onClick={() => setShowNotifs(false)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
                  <X size={14} />
                </button>
              </div>
              <div className="max-h-72 overflow-y-auto">
                {notifications.length === 0 ? (
                  <div className="px-4 py-8 text-center text-sm text-slate-400">
                    No notifications yet
                  </div>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      className={`px-4 py-3 border-b border-slate-50 dark:border-slate-700/40 ${
                        !n.is_read ? 'bg-[#005A70]/5 dark:bg-[#005A70]/10' : ''
                      }`}
                    >
                      <p className="text-sm text-slate-700 dark:text-slate-200 leading-relaxed">{n.message}</p>
                      <p className="text-[10px] text-slate-400 mt-1.5">
                        {new Date(n.created_at).toLocaleDateString('en-IN', {
                          day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
                        })}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        <div className="h-8 w-8 rounded-full bg-[#005A70] flex items-center justify-center text-white text-xs font-semibold">
          {user?.email?.[0]?.toUpperCase() ?? 'U'}
        </div>
      </div>
    </header>
  )
}
