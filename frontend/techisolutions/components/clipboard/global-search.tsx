"use client"

import Link from "next/link"
import { useEffect, useId, useRef } from "react"
import { FileText, Files, Search, X } from "lucide-react"

import { CategoryBadge } from "@/components/clipboard/form-elements"
import { useGlobalSearch } from "@/components/clipboard/global-search-context"
import { cn } from "@/lib/utils"

export function GlobalSearch() {
  const inputId = useId()
  const listId = useId()
  const rootRef = useRef<HTMLDivElement>(null)
  const { query, setQuery, clearQuery, results, loading, open, setOpen } = useGlobalSearch()

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false)
    }
    function onPointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener("keydown", onKeyDown)
    document.addEventListener("mousedown", onPointerDown)
    return () => {
      document.removeEventListener("keydown", onKeyDown)
      document.removeEventListener("mousedown", onPointerDown)
    }
  }, [setOpen])

  const showPanel = open && query.trim().length > 0
  return (
    <div ref={rootRef} className="relative w-full max-w-md min-w-0 flex-1">
      <label htmlFor={inputId} className="sr-only">Buscar consultas y archivos</label>
      <div className="relative">
        <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-institutional" aria-hidden />
        <input id={inputId} type="search" role="combobox" aria-expanded={showPanel} aria-controls={listId} aria-autocomplete="list" autoComplete="off" placeholder="Buscar por pregunta, fuente o archivo…" value={query} onChange={(event) => setQuery(event.target.value)} onFocus={() => { if (query.trim()) setOpen(true) }} onKeyDown={(event) => { if (event.key === "Escape") { event.preventDefault(); clearQuery() } }} className="w-full border-2 border-border bg-paper py-2 pr-9 pl-9 text-sm text-foreground placeholder:text-muted-foreground focus-visible:border-carbon focus-visible:ring-2 focus-visible:ring-carbon/25 focus-visible:outline-none" />
        {query ? <button type="button" onClick={clearQuery} className="absolute top-1/2 right-2 -translate-y-1/2 p-1 text-muted-foreground hover:text-stamp-red" aria-label="Limpiar búsqueda"><X className="size-4" aria-hidden /></button> : null}
      </div>
      {showPanel ? <div id={listId} role="listbox" aria-label="Resultados de búsqueda" className="absolute top-full right-0 left-0 z-50 mt-1 max-h-80 overflow-y-auto border-2 border-institutional bg-card shadow-[4px_4px_0_0_rgba(26,58,92,0.12)]">
        {loading ? <p className="p-4 font-mono text-xs text-muted-foreground">Buscando en el repositorio…</p> : results.length === 0 ? <div className="space-y-2 p-4"><p className="text-sm font-medium text-foreground">Sin resultados para “{query.trim()}”</p><p className="text-xs text-muted-foreground">Prueba otra búsqueda o <Link href="/consultar" className="font-semibold text-carbon hover:underline" onClick={() => setOpen(false)}>consulta el corpus</Link>.</p></div> : <ul className="divide-y divide-border">{results.map((hit) => <li key={`${hit.kind}-${hit.id}`} role="option" aria-selected="false"><Link href={hit.href} onClick={() => setOpen(false)} className={cn("flex gap-3 px-3 py-2.5 transition-colors hover:bg-secondary/60 focus-visible:bg-secondary/60 focus-visible:outline-none")}>{hit.kind === "consulta" ? <><FileText className="mt-0.5 size-4 shrink-0 text-institutional" aria-hidden /><div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold text-institutional">{hit.titulo}</p><div className="mt-1 flex flex-wrap items-center gap-2"><CategoryBadge category={hit.categoria} /><span className="font-mono text-xs font-bold text-institutional">Relevancia {Math.round(hit.relevancia * 100)}%</span></div>{hit.palabrasClave.length > 0 ? <p className="mt-1 truncate font-mono text-[10px] text-muted-foreground">{hit.palabrasClave.slice(0, 4).join(" · ")}</p> : null}</div><span className="shrink-0 font-mono text-[10px] font-bold tracking-wider text-muted-foreground uppercase">Consulta</span></> : <><Files className="mt-0.5 size-4 shrink-0 text-institutional" aria-hidden /><div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold text-institutional">{hit.nombre}</p><p className="mt-1 font-mono text-[10px] text-muted-foreground">{hit.tipo || "archivo"} · {Math.round(hit.tamano / 1024)} KB</p></div><span className="shrink-0 font-mono text-[10px] font-bold tracking-wider text-muted-foreground uppercase">Archivo</span></>}</Link></li>)}</ul>}
      </div> : null}
    </div>
  )
}
