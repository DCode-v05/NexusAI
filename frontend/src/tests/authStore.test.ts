/**
 * Unit tests for src/store/authStore.ts
 * Uses Vitest + jsdom (no React needed — pure Zustand store logic).
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from '../store/authStore'

const TEST_USER = { id: 1, email: 'test@college.edu', role: 'student' as const }
const ACCESS_TOKEN = 'header.payload.signature'
const REFRESH_TOKEN = 'refresh.header.payload.signature'

function resetStore() {
  useAuthStore.getState().logout()
}

describe('authStore', () => {
  beforeEach(() => {
    resetStore()
  })

  describe('initial state', () => {
    it('has no token', () => {
      expect(useAuthStore.getState().token).toBeNull()
    })

    it('has no refreshToken', () => {
      expect(useAuthStore.getState().refreshToken).toBeNull()
    })

    it('has no user', () => {
      expect(useAuthStore.getState().user).toBeNull()
    })

    it('is not authenticated', () => {
      expect(useAuthStore.getState().isAuthenticated()).toBe(false)
    })
  })

  describe('setAuth', () => {
    it('sets token, refreshToken, and user', () => {
      useAuthStore.getState().setAuth(ACCESS_TOKEN, REFRESH_TOKEN, TEST_USER)
      const state = useAuthStore.getState()
      expect(state.token).toBe(ACCESS_TOKEN)
      expect(state.refreshToken).toBe(REFRESH_TOKEN)
      expect(state.user).toEqual(TEST_USER)
    })

    it('makes isAuthenticated return true', () => {
      useAuthStore.getState().setAuth(ACCESS_TOKEN, REFRESH_TOKEN, TEST_USER)
      expect(useAuthStore.getState().isAuthenticated()).toBe(true)
    })

    it('stores correct user role', () => {
      const counselor = { id: 2, email: 'c@hospital.edu', role: 'counselor' as const }
      useAuthStore.getState().setAuth(ACCESS_TOKEN, REFRESH_TOKEN, counselor)
      expect(useAuthStore.getState().user?.role).toBe('counselor')
    })
  })

  describe('setToken', () => {
    it('replaces only the access token', () => {
      useAuthStore.getState().setAuth(ACCESS_TOKEN, REFRESH_TOKEN, TEST_USER)
      const newToken = 'new.access.token'
      useAuthStore.getState().setToken(newToken)
      const state = useAuthStore.getState()
      expect(state.token).toBe(newToken)
      expect(state.refreshToken).toBe(REFRESH_TOKEN)  // unchanged
      expect(state.user).toEqual(TEST_USER)           // unchanged
    })
  })

  describe('logout', () => {
    it('clears token', () => {
      useAuthStore.getState().setAuth(ACCESS_TOKEN, REFRESH_TOKEN, TEST_USER)
      useAuthStore.getState().logout()
      expect(useAuthStore.getState().token).toBeNull()
    })

    it('clears refreshToken', () => {
      useAuthStore.getState().setAuth(ACCESS_TOKEN, REFRESH_TOKEN, TEST_USER)
      useAuthStore.getState().logout()
      expect(useAuthStore.getState().refreshToken).toBeNull()
    })

    it('clears user', () => {
      useAuthStore.getState().setAuth(ACCESS_TOKEN, REFRESH_TOKEN, TEST_USER)
      useAuthStore.getState().logout()
      expect(useAuthStore.getState().user).toBeNull()
    })

    it('makes isAuthenticated return false', () => {
      useAuthStore.getState().setAuth(ACCESS_TOKEN, REFRESH_TOKEN, TEST_USER)
      useAuthStore.getState().logout()
      expect(useAuthStore.getState().isAuthenticated()).toBe(false)
    })
  })

  describe('isAuthenticated', () => {
    it('returns false with no token', () => {
      expect(useAuthStore.getState().isAuthenticated()).toBe(false)
    })

    it('returns true after setAuth', () => {
      useAuthStore.getState().setAuth(ACCESS_TOKEN, REFRESH_TOKEN, TEST_USER)
      expect(useAuthStore.getState().isAuthenticated()).toBe(true)
    })

    it('returns false after logout', () => {
      useAuthStore.getState().setAuth(ACCESS_TOKEN, REFRESH_TOKEN, TEST_USER)
      useAuthStore.getState().logout()
      expect(useAuthStore.getState().isAuthenticated()).toBe(false)
    })
  })
})
