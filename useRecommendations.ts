import { useCallback, useState } from 'react'
import type { Recommendation, UserPreferences } from '@/types'
import { fetchRecommendations } from '@/services/api'

interface UseRecommendationsResult {
  recommendations: Recommendation[]
  loading: boolean
  error: string | null
  runRecommendation: (preferences: UserPreferences) => Promise<void>
}

/** Encapsulates the loading/error/data lifecycle around requesting recommendations. */
export function useRecommendations(): UseRecommendationsResult {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const runRecommendation = useCallback(async (preferences: UserPreferences) => {
    setLoading(true)
    setError(null)
    try {
      const results = await fetchRecommendations(preferences, 12)
      setRecommendations(results)
    } catch (err) {
      setError('Something went wrong generating recommendations. Please try again.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [])

  return { recommendations, loading, error, runRecommendation }
}
