import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Mail, Lock, Activity } from 'lucide-react'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import { useLogin } from '../../hooks/useAuth'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const login = useLogin()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    login.mutate({ email, password })
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-2xl bg-[#005A70] flex items-center justify-center mb-3 shadow-lg shadow-[#005A70]/20">
            <Activity size={22} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">NexusAI</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Student Wellbeing & Career Intelligence</p>
        </div>

        {/* Card */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-card border border-slate-200 dark:border-slate-700 p-8">
          <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-6">Sign in to your account</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Email address"
              type="email"
              placeholder="you@college.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              icon={<Mail size={15} />}
              required
            />
            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              icon={<Lock size={15} />}
              required
            />
            {login.isError && (
              <p className="text-sm text-error bg-red-50 rounded-lg px-3 py-2">
                Invalid email or password. Please try again.
              </p>
            )}
            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={login.isPending}
              className="w-full mt-2"
            >
              Sign In
            </Button>
          </form>
        </div>

        <p className="text-center text-sm text-slate-500 dark:text-slate-400 mt-5">
          Don't have an account?{' '}
          <Link to="/register" className="text-[#005A70] font-medium hover:underline">
            Create one
          </Link>
        </p>
      </div>
    </div>
  )
}
