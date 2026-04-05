import client from './client'

export interface SurveyScores {
  q1_score: number
  q2_score: number
  q3_score: number
  free_text?: string
}

export interface RiskResult {
  score: number
  tier: string
  anomaly_score: number
  sentiment_score: number
  survey_decline: number
}

export interface ChatResponse {
  reply: string
  risk_tier: string
  risk_score?: number
  agent?: string
  helpline?: string
}

export const wellbeingApi = {
  submitSurvey: async (scores: SurveyScores): Promise<RiskResult> => {
    const { data } = await client.post<RiskResult>('/wellbeing/survey', scores)
    return data
  },

  chat: async (message: string): Promise<ChatResponse> => {
    const { data } = await client.post<ChatResponse>('/wellbeing/chat', { message })
    return data
  },

  getRisk: async (studentId: number): Promise<RiskResult | null> => {
    const { data } = await client.get<RiskResult | null>(`/wellbeing/risk/${studentId}`)
    return data
  },
}
