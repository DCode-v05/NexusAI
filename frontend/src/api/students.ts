import client from './client'

export interface BehaviorSignals {
  session_gap_days: number
  survey_skip_streak: number
  avg_session_length: number
  assignment_delay_hrs: number
  chat_initiation_freq: number
  mood_score_trend: number
  login_hour_variance: number
}

export interface DashboardData {
  student_id: number
  name: string
  streak_days: number
  last_seen: string
  behavior: BehaviorSignals | null
  mood_history: MoodEntry[]
  risk_tier: string
}

export interface MoodEntry {
  date: string
  composite: number
}

export const studentsApi = {
  getDashboard: async (): Promise<DashboardData> => {
    const { data } = await client.get<DashboardData>('/students/dashboard')
    return data
  },

  logBehavior: async (signals: Partial<BehaviorSignals>): Promise<void> => {
    await client.post('/students/behavior-log', signals)
  },

  getMoodHistory: async (): Promise<MoodEntry[]> => {
    const { data } = await client.get<MoodEntry[]>('/students/mood-history')
    return data
  },
}
