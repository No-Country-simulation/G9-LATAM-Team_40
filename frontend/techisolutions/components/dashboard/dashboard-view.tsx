"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { Files, Plus, Search } from "lucide-react"

import { AuthGate } from "@/components/auth/auth-gate"
import { AppShell } from "@/components/clipboard/app-shell"
import { RecentDocumentCard, StatCell } from "@/components/clipboard/document-card"
import { ClipboardClipBar, StampAction } from "@/components/clipboard/stamp-action"
import { FormAlert } from "@/components/clipboard/form-field"
import { FormPaper } from "@/components/clipboard/form-elements"
import { useGlobalSearchOptional } from "@/components/clipboard/global-search-context"
import { consultaTitulo } from "@/lib/api-mappers"
import { matchesConsultaQuery } from "@/lib/search"
import { listarArchivos } from "@/services/archivo.service"
import { listarCategorias } from "@/services/categoria.service"
import { listarConsultas } from "@/services/consulta.service"
import type { ConsultaResponse } from "@/types/consulta.types"

export function DashboardView() {
  const search = useGlobalSearchOptional()
  const query = search?.query ?? ""
  const [consultas, setConsultas] = useState<ConsultaResponse[]>([])
  const [stats, setStats] = useState({ consultas: 0, categorias: 0, archivos: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    void (async () => {
      try {
        const [items, categories, files] = await Promise.all([
          listarConsultas(),
          listarCategorias(),
          listarArchivos({ page: 0, size: 1 }),
        ])
        if (!active) return
        setConsultas(items)
        setStats({ consultas: items.length, categorias: categories.length, archivos: files.totalElements })
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "No se pudo cargar el panel.")
      } finally {
        if (active) setLoading(false)
      }
    })()
    return () => { active = false }
  }, [])

  const filtering = query.trim().length > 0
  const recent = consultas.filter((item) => matchesConsultaQuery(item, query)).slice(0, 12)
  return (
    <AuthGate>
      <AppShell currentPath="/dashboard">
        <div className="mb-6"><p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">Registro de análisis · Panel operativo</p><h1 className="text-2xl font-bold text-institutional sm:text-3xl">Centro de acciones</h1><p className="mt-1 max-w-xl text-sm text-foreground">Consulta el corpus normativo, administra tus archivos privados y revisa la evidencia de cada respuesta.</p></div>
        {error ? <FormAlert variant="error" className="mb-4">{error}</FormAlert> : null}
        <ClipboardClipBar>
          <StampAction href="/consultar" icon={Search} label="Consultar corpus" description="Pregunta y conserva fuentes" tone="yellow" />
          <StampAction href="/archivos" icon={Files} label="Archivos privados" description="Sube y reconstruye tu índice" />
        </ClipboardClipBar>
        <section className="mt-8" aria-labelledby="stats-heading"><h2 id="stats-heading" className="mb-4 text-sm font-bold uppercase tracking-wide text-institutional">Resumen de actividad</h2><div className="grid gap-3 sm:grid-cols-3"><StatCell label="Consultas realizadas" value={loading ? "—" : stats.consultas} href="/consultar" /><StatCell label="Categorías de fuentes" value={loading ? "—" : stats.categorias} /><StatCell label="Archivos privados" value={loading ? "—" : stats.archivos} href="/archivos" /></div></section>
        <section className="mt-10" aria-labelledby="recent-heading"><div className="mb-4 flex flex-wrap items-center justify-between gap-3"><h2 id="recent-heading" className="text-lg font-bold text-institutional">Análisis recientes{filtering ? <span className="ml-2 font-mono text-xs font-normal text-muted-foreground">filtro: “{query.trim()}” · {recent.length}</span> : null}</h2><Link href="/consultar" className="inline-flex items-center gap-1.5 text-sm font-semibold text-carbon hover:underline"><Plus className="size-4" aria-hidden />Nueva consulta</Link></div><FormPaper className="p-4 sm:p-5">{loading ? <p className="py-4 font-mono text-sm text-muted-foreground">Cargando análisis…</p> : recent.length === 0 ? <div className="space-y-2 py-4 text-center"><p className="text-sm font-medium text-foreground">{filtering ? `Ningún análisis coincide con “${query.trim()}”.` : "Aún no hay consultas."}</p><p className="text-sm text-muted-foreground">{filtering ? <button type="button" onClick={() => search?.clearQuery()} className="font-semibold text-carbon hover:underline">Limpiar filtro</button> : <Link href="/consultar" className="font-semibold text-carbon hover:underline">Hacer una consulta</Link>}</p></div> : <div className="grid gap-4 sm:grid-cols-2">{recent.map((item) => <RecentDocumentCard key={item.id} titulo={consultaTitulo(item)} categoria={item.categoriaFuentePrincipal} relevancia={item.relevancia} palabras_clave={item.palabrasClave} procesado_en={item.procesadoEn} href={`/consultar?consulta=${encodeURIComponent(item.id)}`} />)}</div>}</FormPaper></section>
      </AppShell>
    </AuthGate>
  )
}
