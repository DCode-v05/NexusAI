/**
 * Tests for the deterministic skill hash used by the SkillRadarChart.
 * The hash function lives inline in PathwayAIPage.tsx — we replicate it here
 * to keep tests self-contained and fast.
 */
import { describe, it, expect } from 'vitest'

// Exact replica of the hash used in PathwayAIPage.tsx
function hashSkill(s: string): number {
  let h = 0
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) & 0xffff
  return (h % 5) + 4
}

describe('hashSkill (SkillRadarChart deterministic scorer)', () => {
  it('returns a value in range [4, 8]', () => {
    const skills = ['Python', 'React', 'SQL', 'ML', 'Docker', 'TypeScript', 'Git']
    for (const s of skills) {
      const score = hashSkill(s)
      expect(score).toBeGreaterThanOrEqual(4)
      expect(score).toBeLessThanOrEqual(8)
    }
  })

  it('is deterministic — same skill always gives same score', () => {
    expect(hashSkill('Python')).toBe(hashSkill('Python'))
    expect(hashSkill('React')).toBe(hashSkill('React'))
    expect(hashSkill('SQL')).toBe(hashSkill('SQL'))
  })

  it('different skills can produce different scores', () => {
    const scores = new Set(['Python', 'React', 'SQL', 'ML', 'Docker', 'Java', 'Go'].map(hashSkill))
    // With 7 skills over a range of 5 values, not all will be the same
    expect(scores.size).toBeGreaterThan(1)
  })

  it('returns an integer', () => {
    expect(Number.isInteger(hashSkill('Python'))).toBe(true)
  })

  it('handles empty string without error', () => {
    const score = hashSkill('')
    expect(score).toBeGreaterThanOrEqual(4)
    expect(score).toBeLessThanOrEqual(8)
  })
})
