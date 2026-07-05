/**
 * Client-side hybrid recommendation engine.
 *
 * This mirrors the Python implementation in
 * `backend/recommendation_engine/` so the app remains fully interactive
 * (e.g. for a static GitHub Pages / portfolio demo) even without the
 * FastAPI backend running. When `VITE_API_BASE_URL` is set and reachable,
 * `services/api.ts` prefers the real backend instead.
 */

import type { Product, Recommendation, UserPreferences } from '@/types'
import productsData from '@/assets/data/products.json'
import usersData from '@/assets/data/users.json'

const BUDGET_RANGES: Record<string, [number, number]> = {
  low: [0, 60],
  medium: [40, 180],
  high: [150, 100000],
}

const WEIGHTS = {
  category: 0.3,
  interest: 0.2,
  budget: 0.2,
  brand: 0.15,
  rating: 0.15,
}

interface RawUser {
  id: number
  interests: string[]
  purchase_history: number[]
  interactions: { product_id: number; action: string; timestamp: string }[]
}

const products = productsData as unknown as (Product & { interest: string })[]
const users = usersData as unknown as RawUser[]

function categoryScore(p: Product, categories: string[]) {
  return categories.includes(p.category) ? 1 : 0
}
function interestScore(p: Product & { interest: string }, interests: string[]) {
  return interests.includes(p.interest) ? 1 : 0
}
function budgetScore(p: Product, budget: string) {
  const [lo, hi] = BUDGET_RANGES[budget] ?? [0, 100000]
  if (p.price >= lo && p.price <= hi) return 1
  const distance = Math.min(Math.abs(p.price - lo), Math.abs(p.price - hi))
  return Math.max(0, 1 - distance / 200)
}
function brandScore(p: Product, brands: string[]) {
  return brands.includes(p.brand) ? 1 : 0.3
}
function ratingScore(p: Product, minRating: number) {
  if (p.rating >= minRating) return Math.min(1, 0.7 + (p.rating - minRating) * 0.3)
  return Math.max(0, 0.5 - (minRating - p.rating) * 0.4)
}

function contentScore(p: Product & { interest: string }, prefs: UserPreferences) {
  return (
    WEIGHTS.category * categoryScore(p, prefs.categories) +
    WEIGHTS.interest * interestScore(p, prefs.interests) +
    WEIGHTS.budget * budgetScore(p, prefs.budget) +
    WEIGHTS.brand * brandScore(p, prefs.brands) +
    WEIGHTS.rating * ratingScore(p, prefs.min_rating)
  )
}

function explainMatch(p: Product & { interest: string }, prefs: UserPreferences): string {
  if (p.category && prefs.categories.includes(p.category)) {
    return `Matches your interest in ${p.category}`
  }
  if (prefs.interests.includes(p.interest)) {
    return `Aligned with your '${p.interest}' interest`
  }
  if (prefs.brands.includes(p.brand)) {
    return `From ${p.brand}, one of your preferred brands`
  }
  if (p.rating >= prefs.min_rating) {
    return `Highly rated at ${p.rating}★ among shoppers like you`
  }
  return 'Recommended because users with similar interests liked this product.'
}

function buildInteractionVector(user: RawUser): Map<number, number> {
  const weight: Record<string, number> = { view: 1, click: 2, add_to_cart: 3, purchase: 5 }
  const vec = new Map<number, number>()
  for (const pid of user.purchase_history) {
    vec.set(pid, (vec.get(pid) ?? 0) + 5)
  }
  for (const i of user.interactions) {
    vec.set(i.product_id, (vec.get(i.product_id) ?? 0) + (weight[i.action] ?? 1))
  }
  return vec
}

function cosineSim(a: Map<number, number>, b: Map<number, number>): number {
  let dot = 0
  for (const [k, v] of a) {
    if (b.has(k)) dot += v * (b.get(k) as number)
  }
  const normA = Math.sqrt([...a.values()].reduce((s, v) => s + v * v, 0))
  const normB = Math.sqrt([...b.values()].reduce((s, v) => s + v * v, 0))
  if (normA === 0 || normB === 0) return 0
  return dot / (normA * normB)
}

function collaborativeScores(targetUser: RawUser | undefined): Map<number, number> {
  if (!targetUser) return new Map()
  const targetVec = buildInteractionVector(targetUser)
  if (targetVec.size === 0) return new Map()

  const sims = users
    .filter((u) => u.id !== targetUser.id)
    .map((u) => ({ user: u, sim: cosineSim(targetVec, buildInteractionVector(u)) }))
    .filter((x) => x.sim > 0)
    .sort((a, b) => b.sim - a.sim)
    .slice(0, 8)

  const owned = new Set(targetUser.purchase_history)
  const raw = new Map<number, number>()
  for (const { user, sim } of sims) {
    const vec = buildInteractionVector(user)
    for (const [pid, w] of vec) {
      if (owned.has(pid)) continue
      raw.set(pid, (raw.get(pid) ?? 0) + sim * w)
    }
  }
  const max = Math.max(1, ...raw.values())
  const normalized = new Map<number, number>()
  for (const [pid, v] of raw) normalized.set(pid, v / max)
  return normalized
}

function adaptiveAlpha(user: RawUser | undefined): number {
  if (!user) return 1
  const len = user.purchase_history.length + user.interactions.length
  if (len === 0) return 1
  if (len < 10) return 0.8
  if (len < 25) return 0.65
  return 0.5
}

/** Generates ranked, explainable recommendations entirely client-side. */
export function generateRecommendationsLocally(
  prefs: UserPreferences,
  topN = 12,
): Recommendation[] {
  const targetUser = prefs.user_id ? users.find((u) => u.id === prefs.user_id) : undefined
  const collabScores = collaborativeScores(targetUser)
  const alpha = collabScores.size > 0 ? adaptiveAlpha(targetUser) : 1

  const ranked: Recommendation[] = products
    .filter((p) => p.in_stock)
    .map((p) => {
      const c = contentScore(p, prefs)
      const cf = collabScores.get(p.id) ?? 0
      let final = alpha * c + (1 - alpha) * cf
      final = 0.92 * final + 0.08 * p.popularity_score
      return {
        ...p,
        match_score: Math.round(final * 100),
        explanation: explainMatch(p, prefs),
        score_breakdown: {
          content_based: Math.round(c * 100),
          collaborative: Math.round(cf * 100),
          blend_alpha: Math.round(alpha * 100) / 100,
        },
      }
    })
    .sort((a, b) => b.match_score - a.match_score)

  return ranked.slice(0, topN)
}

export function getAllProductsLocally(): Product[] {
  return products
}

export function getFilterOptionsLocally() {
  return {
    categories: [...new Set(products.map((p) => p.category))].sort(),
    brands: [...new Set(products.map((p) => p.brand))].sort(),
  }
}
