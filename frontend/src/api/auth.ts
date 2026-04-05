import client from './client'
import { AuthUser } from '../store/authStore'

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export const authApi = {
  login: async (email: string, password: string): Promise<LoginResponse> => {
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)
    const { data } = await client.post<LoginResponse>('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return data
  },

  register: async (email: string, password: string, role: string): Promise<AuthUser> => {
    const { data } = await client.post<AuthUser>('/auth/register', { email, password, role })
    return data
  },

  me: async (token?: string): Promise<AuthUser> => {
    const headers = token ? { Authorization: `Bearer ${token}` } : {}
    const { data } = await client.get<AuthUser>('/auth/me', { headers })
    return data
  },

  refresh: async (refreshToken: string): Promise<LoginResponse> => {
    const { data } = await client.post<LoginResponse>('/auth/refresh', { refresh_token: refreshToken })
    return data
  },

  logout: async (): Promise<void> => {
    // Best-effort — revokes current access token on the server
    await client.post('/auth/logout').catch(() => {})
  },
}
