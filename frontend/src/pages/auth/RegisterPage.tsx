import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Mail, Lock, User, Activity } from 'lucide-react'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import { useRegister } from '../../hooks/useAuth'

export default function RegisterPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<'student' | 'counselor'>('student')
  const register = useRegister()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    register.mutate({ email, password, role })
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-2xl bg-[#005A70] flex items-center justify-center mb-3 shadow-lg shadow-[#005A70]/20">
            <Activity size={22} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">NexusAI</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Create your account</p>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-card border border-slate-200 dark:border-slate-700 p-8">
          <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-6">Join NexusAI</h2>
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
              placeholder="Min. 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              icon={<Lock size={15} />}
              required
              minLength={8}
            />

            {/* Role selector */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-1.5">I am a</label>
              <div className="grid grid-cols-2 gap-2">
                {(['student', 'counselor'] as const).map((r) => (
                  <button
                    key={r}
                    type="button"
                    onClick={() => setRole(r)}
                    className={`py-2.5 rounded-lg text-sm font-medium border transition-all ${
                      role === r
                        ? 'bg-[#005A70] text-white border-[#005A70]'
                        : 'bg-white dark:bg-slate-700 text-slate-600 dark:text-slate-300 border-slate-300 dark:border-slate-600 hover:border-[#005A70] hover:text-[#005A70]'
                    }`}
                  >
                    <User size={14} className="inline mr-1.5 -mt-0.5" />
                    {r.charAt(0).toUpperCase() + r.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {register.isError && (
              <p className="text-sm text-error bg-red-50 rounded-lg px-3 py-2">
                Registration failed. Email may already exist.
              </p>
            )}
            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={register.isPending}
              className="w-full mt-2"
            >
              Create Account
            </Button>
          </form>
        </div>

        <p className="text-center text-sm text-slate-500 dark:text-slate-400 mt-5">
          Already have an account?{' '}
          <Link to="/login" className="text-[#005A70] font-medium hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
