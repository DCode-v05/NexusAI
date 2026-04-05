import client from './client'

export interface SkillProfile {
  skills: string[]
  target_role: string
  experience_level: string
}

export interface RoadmapResponse {
  roadmap: string
  weeks: WeekPlan[]
  skill_gaps: string[]
}

export interface WeekPlan {
  week: number
  title: string
  tasks: string[]
  resources: string[]
}

export interface JobOpening {
  role: string
  company: string
  location: string
  required_skills: string[]
  min_salary_lpa: number
  max_salary_lpa: number
  demand_score: number
  experience_level: string
  source: string
}

export const pathwayApi = {
  uploadResume: async (file: File): Promise<SkillProfile> => {
    const form = new FormData()
    form.append('file', file)
    const { data } = await client.post<SkillProfile>('/pathway/resume', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  generateRoadmap: async (skills: string[], targetRole: string): Promise<RoadmapResponse> => {
    const { data } = await client.post<RoadmapResponse>('/pathway/generate-roadmap', {
      target_role: targetRole,
    })
    return data
  },

  getJobOpenings: async (skills: string[], role: string): Promise<JobOpening[]> => {
    const { data } = await client.post<JobOpening[]>('/pathway/job-openings', {
      skills,
      target_role: role,
    })
    return data
  },

  getMockInterview: async (role: string): Promise<{ question: string }> => {
    const { data } = await client.get<{ question: string }>(`/pathway/mock-interview/${encodeURIComponent(role)}`)
    return data
  },
}
