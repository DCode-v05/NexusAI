import client from './client'

export interface CaseNoteItem {
  id: number
  alert_id: number
  note_text: string
  created_at: string
}

export interface AlertCard {
  alert_id: number
  student_id: number
  risk_score: number
  tier: string
  anomaly_score: number
  sentiment_score: number
  trigger_message?: string
  created_at: string
  is_resolved: boolean
  student_name?: string
  notes: CaseNoteItem[]
}

export interface NotificationItem {
  id: number
  message: string
  is_read: boolean
  created_at: string
}

export const counselorApi = {
  getAlerts: async (threshold = 0.4): Promise<AlertCard[]> => {
    const { data } = await client.get<AlertCard[]>('/counselor/alerts', {
      params: { threshold },
    })
    return data
  },

  addNote: async (alertId: number, noteText: string): Promise<CaseNoteItem> => {
    const { data } = await client.post<CaseNoteItem>('/counselor/notes', { alert_id: alertId, note_text: noteText })
    return data
  },

  resolveAlert: async (alertId: number, notes?: string): Promise<void> => {
    await client.post('/counselor/resolve', { alert_id: alertId, resolution_notes: notes })
  },

  getNotifications: async (): Promise<NotificationItem[]> => {
    const { data } = await client.get<NotificationItem[]>('/counselor/notifications')
    return data
  },

  markNotificationsRead: async (): Promise<void> => {
    await client.post('/counselor/notifications/read')
  },
}
