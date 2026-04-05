import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Brain, Rocket, Users, LogOut, Activity,
} from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import { useLogout } from '../../hooks/useAuth'

interface NavItem {
  to: string
  icon: React.ReactNode
  label: string
  roles?: string[]
}

const navItems: NavItem[] = [
  { to: '/dashboard',  icon: <LayoutDashboard size={18} />, label: 'Dashboard',   roles: ['student'] },
  { to: '/mindbridge', icon: <Brain size={18} />,           label: 'MindBridge',  roles: ['student'] },
  { to: '/pathway',    icon: <Rocket size={18} />,          label: 'PathwayAI',   roles: ['student'] },
  { to: '/counselor',  icon: <Users size={18} />,           label: 'Counselor',   roles: ['counselor', 'admin'] },
]

export default function Sidebar() {
  const { user } = useAuthStore()
  const { mutate: handleLogout } = useLogout()

  const filtered = navItems.filter(
    (item) => !item.roles || item.roles.includes(user?.role ?? '')
  )

  return (
    <aside className="w-60 shrink-0 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-700/60 flex flex-col h-full">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-slate-100 dark:border-slate-700/60">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#005A70] flex items-center justify-center">
            <Activity size={16} className="text-white" />
          </div>
          <div>
            <span className="font-bold text-slate-800 dark:text-slate-100 text-sm">NexusAI</span>
            <p className="text-[10px] text-slate-400 leading-none">Student Intelligence</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-3 space-y-0.5">
        {filtered.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150 ${
                isActive
                  ? 'bg-[#005A70]/10 text-[#005A70] dark:bg-[#005A70]/20 dark:text-teal-300'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-800 dark:hover:text-slate-200'
              }`
            }
          >
            {item.icon}
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* User footer */}
      <div className="p-3 border-t border-slate-100 dark:border-slate-700/60">
        <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg">
          <div className="w-7 h-7 rounded-full bg-[#005A70]/15 flex items-center justify-center text-[#005A70] dark:text-teal-300 text-xs font-semibold">
            {user?.email?.[0]?.toUpperCase() ?? 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-slate-700 dark:text-slate-300 truncate">{user?.email}</p>
            <p className="text-[10px] text-slate-400 capitalize">{user?.role}</p>
          </div>
          <button
            onClick={() => handleLogout()}
            className="text-slate-400 hover:text-error transition-colors"
            title="Logout"
          >
            <LogOut size={15} />
          </button>
        </div>
      </div>
    </aside>
  )
}
