import { useEffect, useMemo, useState } from 'react'
import type { FilterState, Product } from '@/types'
import { fetchFilterOptions, fetchProducts } from '@/services/api'

const DEFAULT_FILTERS: FilterState = {
  category: null,
  brand: null,
  min_price: null,
  max_price: null,
  min_rating: null,
  in_stock_only: false,
  sort_by: null,
  search: '',
}

export function useProductFilters() {
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS)
  const [products, setProducts] = useState<Product[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [brands, setBrands] = useState<string[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchFilterOptions().then(({ categories, brands }) => {
      setCategories(categories)
      setBrands(brands)
    })
  }, [])

  useEffect(() => {
    setLoading(true)
    const handle = setTimeout(() => {
      fetchProducts(filters)
        .then(setProducts)
        .finally(() => setLoading(false))
    }, 200) // debounce so typing in search doesn't spam requests
    return () => clearTimeout(handle)
  }, [filters])

  const activeFilterCount = useMemo(
    () =>
      Object.entries(filters).filter(([key, value]) => {
        if (key === 'search') return false
        if (key === 'in_stock_only') return value === true
        return value !== null && value !== ''
      }).length,
    [filters],
  )

  function updateFilter<K extends keyof FilterState>(key: K, value: FilterState[K]) {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }

  function resetFilters() {
    setFilters(DEFAULT_FILTERS)
  }

  return { filters, updateFilter, resetFilters, products, categories, brands, loading, activeFilterCount }
}
