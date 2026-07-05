import { useEffect, useState } from 'react'

type Theme = 'dark' | 'light'
const STORAGE_KEY = 'signal:theme'

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem(STORAGE_KEY) as Theme | null
    return saved ?? 'dark'
  })

  useEffect(() => {
    const root = document.documentElement
    root.classList.toggle('dark', theme === 'dark')
    root.classList.toggle('light', theme === 'light')
    localStorage.setItem(STORAGE_KEY, theme)
  }, [theme])

  function toggleTheme() {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))
  }

  return { theme, toggleTheme }
}
