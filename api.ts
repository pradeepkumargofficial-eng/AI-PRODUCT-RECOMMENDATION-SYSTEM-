import type {
  AnalyticsDashboard,
  FilterState,
  Product,
  Recommendation,
  SimpleUser,
  UserPreferences,
} from '@/types'
import {
  generateRecommendationsLocally,
  getAllProductsLocally,
  getFilterOptionsLocally,
} from './recommendationEngine'

const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL || '/api'

/** Small helper to keep fetch calls terse and consistently error-handled. */
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    throw new Error(`API request failed: ${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<T>
}

/**
 * Tracks whether the FastAPI backend is reachable. If a call fails (e.g. the
 * backend isn't running - common when this project is deployed as a static
 * frontend-only demo), the app transparently falls back to the client-side
 * recommendation engine so the experience never breaks.
 */
let backendAvailable = true

export async function fetchRecommendations(
  preferences: UserPreferences,
  topN = 12,
): Promise<Recommendation[]> {
  if (backendAvailable) {
    try {
      const data = await request<{ recommendations: Recommendation[] }>('/recommendations', {
        method: 'POST',
        body: JSON.stringify({ preferences, top_n: topN }),
      })
      return data.recommendations
    } catch (err) {
      console.warn('Backend unreachable, falling back to local recommendation engine.', err)
      backendAvailable = false
    }
  }
  return generateRecommendationsLocally(preferences, topN)
}

export async function fetchProducts(filters: Partial<FilterState> = {}): Promise<Product[]> {
  if (backendAvailable) {
    try {
      const params = new URLSearchParams()
      if (filters.category) params.set('category', filters.category)
      if (filters.brand) params.set('brand', filters.brand)
      if (filters.min_price != null) params.set('min_price', String(filters.min_price))
      if (filters.max_price != null) params.set('max_price', String(filters.max_price))
      if (filters.min_rating != null) params.set('min_rating', String(filters.min_rating))
      if (filters.in_stock_only) params.set('in_stock_only', 'true')
      if (filters.sort_by) params.set('sort_by', filters.sort_by)
      if (filters.search) params.set('search', filters.search)

      const data = await request<{ products: Product[] }>(`/products?${params.toString()}`)
      return data.products
    } catch (err) {
      console.warn('Backend unreachable, falling back to local product data.', err)
      backendAvailable = false
    }
  }

  let items = getAllProductsLocally()
  if (filters.category) items = items.filter((p) => p.category === filters.category)
  if (filters.brand) items = items.filter((p) => p.brand === filters.brand)
  if (filters.min_price != null) items = items.filter((p) => p.price >= filters.min_price!)
  if (filters.max_price != null) items = items.filter((p) => p.price <= filters.max_price!)
  if (filters.min_rating != null) items = items.filter((p) => p.rating >= filters.min_rating!)
  if (filters.in_stock_only) items = items.filter((p) => p.in_stock)
  if (filters.search) {
    const q = filters.search.toLowerCase()
    items = items.filter(
      (p) => p.name.toLowerCase().includes(q) || p.description.toLowerCase().includes(q),
    )
  }
  if (filters.sort_by === 'price') items = [...items].sort((a, b) => a.price - b.price)
  if (filters.sort_by === 'rating') items = [...items].sort((a, b) => b.rating - a.rating)
  if (filters.sort_by === 'popularity')
    items = [...items].sort((a, b) => b.popularity_score - a.popularity_score)
  return items
}

export async function fetchFilterOptions(): Promise<{ categories: string[]; brands: string[] }> {
  if (backendAvailable) {
    try {
      return await request('/meta/filters')
    } catch {
      backendAvailable = false
    }
  }
  return getFilterOptionsLocally()
}

export async function fetchAnalytics(): Promise<AnalyticsDashboard | null> {
  try {
    return await request<AnalyticsDashboard>('/analytics/dashboard')
  } catch (err) {
    console.warn('Analytics dashboard requires the backend to be running.', err)
    return null
  }
}

export async function fetchInsights(): Promise<string[]> {
  try {
    const data = await request<{ insights: string[] }>('/analytics/insights')
    return data.insights
  } catch (err) {
    console.warn('Insights require the backend to be running.', err)
    return []
  }
}

export async function fetchUsers(): Promise<SimpleUser[]> {
  try {
    return await request<SimpleUser[]>('/users')
  } catch {
    return []
  }
}
