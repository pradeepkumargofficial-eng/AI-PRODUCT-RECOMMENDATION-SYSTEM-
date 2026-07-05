import { useCallback, useEffect, useState } from 'react'

const STORAGE_KEY = 'signal:favorites'

/** Persists a user's favorited product IDs across sessions via localStorage. */
export function useFavorites() {
  const [favorites, setFavorites] = useState<number[]>(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      return raw ? (JSON.parse(raw) as number[]) : []
    } catch {
      return []
    }
  })

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(favorites))
  }, [favorites])

  const toggleFavorite = useCallback((productId: number) => {
    setFavorites((prev) =>
      prev.includes(productId) ? prev.filter((id) => id !== productId) : [...prev, productId],
    )
  }, [])

  const isFavorite = useCallback((productId: number) => favorites.includes(productId), [favorites])

  return { favorites, toggleFavorite, isFavorite }
}
