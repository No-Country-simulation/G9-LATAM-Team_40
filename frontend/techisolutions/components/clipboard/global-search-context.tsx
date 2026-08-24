"use client"

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"

import { searchRemote, type SearchHit } from "@/lib/search"

interface GlobalSearchContextValue {
  query: string
  setQuery: (value: string) => void
  clearQuery: () => void
  results: SearchHit[]
  loading: boolean
  open: boolean
  setOpen: (open: boolean) => void
}

const GlobalSearchContext = createContext<GlobalSearchContextValue | null>(
  null
)

export function GlobalSearchProvider({ children }: { children: ReactNode }) {
  const [query, setQueryState] = useState("")
  const [open, setOpen] = useState(false)
  const [results, setResults] = useState<SearchHit[]>([])
  const [loading, setLoading] = useState(false)

  const setQuery = useCallback((value: string) => {
    setQueryState(value)
    setOpen(value.trim().length > 0)
  }, [])

  const clearQuery = useCallback(() => {
    setQueryState("")
    setOpen(false)
    setResults([])
  }, [])

  useEffect(() => {
    const q = query.trim()
    if (!q) return

    let cancelled = false
    const timer = window.setTimeout(() => {
      setLoading(true)
      void searchRemote(q)
        .then((hits) => {
          if (!cancelled) setResults(hits)
        })
        .catch(() => {
          if (!cancelled) setResults([])
        })
        .finally(() => {
          if (!cancelled) setLoading(false)
        })
    }, 300)

    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [query])

  const value = useMemo(() => {
    const trimmed = query.trim()
    return {
      query,
      setQuery,
      clearQuery,
      results: trimmed ? results : [],
      loading: Boolean(trimmed) && loading,
      open,
      setOpen,
    }
  }, [query, setQuery, clearQuery, results, loading, open])

  return (
    <GlobalSearchContext.Provider value={value}>
      {children}
    </GlobalSearchContext.Provider>
  )
}

export function useGlobalSearch() {
  const ctx = useContext(GlobalSearchContext)
  if (!ctx) {
    throw new Error("useGlobalSearch must be used within GlobalSearchProvider")
  }
  return ctx
}

export function useGlobalSearchOptional() {
  return useContext(GlobalSearchContext)
}
