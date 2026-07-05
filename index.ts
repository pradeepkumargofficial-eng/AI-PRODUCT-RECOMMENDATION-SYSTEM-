export interface Product {
  id: number
  name: string
  category: string
  brand: string
  description: string
  price: number
  rating: number
  num_reviews: number
  tags: string[]
  in_stock: boolean
  popularity_score: number
  image_seed: number
}

export interface ScoreBreakdown {
  content_based: number
  collaborative: number
  blend_alpha: number
}

export interface Recommendation extends Product {
  match_score: number
  explanation: string
  score_breakdown: ScoreBreakdown
}

export type Budget = 'low' | 'medium' | 'high'
export type Goal = 'explore' | 'gift' | 'upgrade' | 'restock'

export interface UserPreferences {
  user_id?: number | null
  categories: string[]
  interests: string[]
  budget: Budget
  brands: string[]
  min_rating: number
  goal: Goal
}

export interface FilterState {
  category: string | null
  brand: string | null
  min_price: number | null
  max_price: number | null
  min_rating: number | null
  in_stock_only: boolean
  sort_by: 'price' | 'rating' | 'popularity' | null
  search: string
}

export interface CategoryPopularity {
  category: string
  count: number
  share: number
}

export interface EngagementPoint {
  month: string
  interactions: number
}

export interface AnalyticsDashboard {
  category_popularity: CategoryPopularity[]
  engagement_trend: EngagementPoint[]
  action_breakdown: Record<string, number>
  recommendation_accuracy: {
    estimated_accuracy_pct: number
    sample_size: number
    method: string
  }
  top_products: Product[]
}

export interface SimpleUser {
  id: number
  name: string
  interests: string[]
}
