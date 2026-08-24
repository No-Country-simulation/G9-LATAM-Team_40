"use client"

import Link from "next/link"
import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { Network, RefreshCw } from "lucide-react"

import { AuthGate } from "@/components/auth/auth-gate"
import { AppShell } from "@/components/clipboard/app-shell"
import { FormAlert } from "@/components/clipboard/form-field"
import { GraphCategoryNavigator } from "@/components/grafo/graph-category-navigator"
import { GraphInspector } from "@/components/grafo/graph-inspector"
import { GraphObservatoryCanvas } from "@/components/grafo/graph-observatory-canvas"
import { GraphSnapshotDrawer } from "@/components/grafo/graph-snapshot-drawer"
import { GraphDrawer } from "@/components/grafo/graph-drawer"
import styles from "@/components/grafo/graph-observatory.module.css"
import { ApiError } from "@/lib/api"
import {
  buildGraphExplorerIndex,
  buildGraphRagView,
  filterGraphExplorer,
  getGraphStats,
  type GraphNode,
} from "@/lib/graph-data"
import {
  buscarGrafosPorFecha,
  listarHistorialGrafos,
  obtenerGrafoActual,
  obtenerGrafoPrivado,
  obtenerGrafoPorId,
} from "@/services/grafo.service"
import { obtenerIndice } from "@/services/indice.service"
import type { GrafoResponse } from "@/types/grafo.types"
import type { IndiceEstado } from "@/types/indice.types"

type GraphScope = "BASE" | "PRIVATE"

function isMissingGrafo(err: unknown): boolean {
  if (!(err instanceof ApiError)) return false
  if (err.status === 404) return true
  return /grafo/i.test(err.message)
}

function isActiveIndex(status: IndiceEstado | null): boolean {
  return (
    status?.estado === "DIRTY" ||
    status?.estado === "QUEUED" ||
    status?.estado === "RUNNING"
  )
}

function formatSnapshotDate(snapshot: GrafoResponse | null): string {
  if (!snapshot?.fechaCreacion) return "Sin fecha registrada"
  return new Date(snapshot.fechaCreacion).toLocaleString("es-CL")
}

function ObservatorySkeleton() {
  return (
    <div className="space-y-3" aria-label="Cargando observatorio" role="status">
      <div className="h-12 border border-border bg-muted" />
      <div className="grid gap-3 xl:grid-cols-[18rem_minmax(0,1fr)_21rem]">
        <div className="hidden h-[calc(100svh-13rem)] min-h-[620px] border border-border bg-muted xl:block" />
        <div className="h-[58svh] min-h-[420px] border border-border bg-muted xl:h-[calc(100svh-13rem)] xl:min-h-[620px]" />
        <div className="hidden h-[calc(100svh-13rem)] min-h-[620px] border border-border bg-muted xl:block" />
      </div>
      <p className="font-mono text-xs text-muted-foreground">Cargando snapshot…</p>
    </div>
  )
}

function EmptyGraphState({
  scope,
  onRetry,
}: {
  scope: GraphScope
  onRetry: () => void
}) {
  return (
    <section className="border-2 border-institutional bg-card p-8 text-center sm:p-12">
      <Network className="mx-auto mb-4 size-10 text-institutional" aria-hidden />
      <h2 className="text-lg font-bold text-institutional">
        {scope === "PRIVATE"
          ? "Tu corpus aún no tiene un grafo publicado."
          : "El corpus base todavía no tiene un snapshot disponible."}
      </h2>
      <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-muted-foreground">
        {scope === "PRIVATE"
          ? "Sube documentos para construir y publicar tu índice privado."
          : "Cuando exista una publicación base podrás explorar categorías, subnodos y relaciones aquí."}
      </p>
      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-2 border-2 border-institutional px-4 py-2 text-sm font-bold text-institutional"
        >
          <RefreshCw className="size-4" aria-hidden />
          Reintentar
        </button>
        {scope === "PRIVATE" ? (
          <Link
            href="/archivos"
            className="border-2 border-sst-yellow bg-sst-yellow px-4 py-2 text-sm font-bold text-institutional"
          >
            Subir documentos
          </Link>
        ) : null}
      </div>
    </section>
  )
}

function Stat({
  label,
  value,
}: {
  label: string
  value: number
}) {
  return (
    <div className={styles.stat}>
      <span className={styles.statValue}>{value}</span>
      <span className={styles.statLabel}>{label}</span>
    </div>
  )
}

export function GrafoView() {
  const exploreTriggerRef = useRef<HTMLButtonElement>(null)
  const snapshotTriggerRef = useRef<HTMLButtonElement>(null)
  const [scope, setScope] = useState<GraphScope>("BASE")
  const [snapshot, setSnapshot] = useState<GrafoResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [missing, setMissing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(
    null
  )
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [query, setQuery] = useState("")
  const [categoriesOpen, setCategoriesOpen] = useState(false)
  const [snapshotsOpen, setSnapshotsOpen] = useState(false)
  const [reduceMotion, setReduceMotion] = useState(false)

  const [historial, setHistorial] = useState<GrafoResponse[]>([])
  const [histPage, setHistPage] = useState(0)
  const [histTotalPages, setHistTotalPages] = useState(0)
  const [histLoading, setHistLoading] = useState(false)
  const [desde, setDesde] = useState("")
  const [hasta, setHasta] = useState("")
  const [dateResults, setDateResults] = useState<GrafoResponse[] | null>(null)
  const [indexStatus, setIndexStatus] = useState<IndiceEstado | null>(null)

  const json = snapshot?.jsonData ?? null
  const index = useMemo(() => buildGraphExplorerIndex(json), [json])
  const filteredIndex = useMemo(
    () => filterGraphExplorer(index, query),
    [index, query]
  )
  const stats = useMemo(() => getGraphStats(json), [json])
  const graph = useMemo(
    () => buildGraphRagView(json, selectedCategoryId, selectedNodeId),
    [json, selectedCategoryId, selectedNodeId]
  )
  const selectedCategory = useMemo(
    () =>
      index.find((category) => category.id === selectedCategoryId) ??
      index.find((category) =>
        category.children.some((child) => child.id === selectedNodeId)
      ) ??
      null,
    [index, selectedCategoryId, selectedNodeId]
  )
  const selectedChild = useMemo(
    () =>
      selectedCategory?.children.find(
        (child) => child.id === selectedNodeId
      ) ?? null,
    [selectedCategory, selectedNodeId]
  )

  const loadActual = useCallback(async (nextScope: GraphScope) => {
    setLoading(true)
    setError(null)
    setMissing(false)
    try {
      const data =
        nextScope === "PRIVATE"
          ? await obtenerGrafoPrivado()
          : await obtenerGrafoActual()
      setSnapshot(data)
      setSelectedCategoryId(null)
      setSelectedNodeId(null)
    } catch (err) {
      if (isMissingGrafo(err)) {
        setSnapshot(null)
        setMissing(true)
      } else {
        setError(
          err instanceof Error
            ? err.message
            : "No se pudo cargar el snapshot actual."
        )
      }
    } finally {
      setLoading(false)
    }
  }, [])

  const loadHistorial = useCallback(async (page = 0) => {
    setHistLoading(true)
    try {
      const data = await listarHistorialGrafos(page, 8)
      setHistorial(data.content)
      setHistPage(data.number)
      setHistTotalPages(data.totalPages)
    } catch (err) {
      setHistorial([])
      setHistTotalPages(0)
      setError(
        err instanceof Error
          ? err.message
          : "No se pudo cargar el historial de snapshots."
      )
    } finally {
      setHistLoading(false)
    }
  }, [])

  const loadIndexStatus = useCallback(async () => {
    try {
      setIndexStatus(await obtenerIndice())
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "No se pudo consultar el estado del índice."
      )
    }
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadActual(scope)
      if (scope === "BASE") void loadHistorial(0)
      else {
        setHistorial([])
        setHistPage(0)
        setHistTotalPages(0)
      }
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadActual, loadHistorial, scope])

  useEffect(() => {
    if (scope !== "PRIVATE") return
    const timer = window.setTimeout(() => void loadIndexStatus(), 0)
    return () => window.clearTimeout(timer)
  }, [loadIndexStatus, scope])

  useEffect(() => {
    if (scope !== "PRIVATE" || !isActiveIndex(indexStatus)) return
    const timer = window.setInterval(() => void loadIndexStatus(), 5000)
    return () => window.clearInterval(timer)
  }, [indexStatus, loadIndexStatus, scope])

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)")
    const handleMotionChange = () => setReduceMotion(mediaQuery.matches)
    handleMotionChange()
    mediaQuery.addEventListener("change", handleMotionChange)
    return () => mediaQuery.removeEventListener("change", handleMotionChange)
  }, [])

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (
        event.key === "Escape" &&
        !categoriesOpen &&
        !snapshotsOpen
      ) {
        setSelectedNodeId(null)
      }
    }
    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [categoriesOpen, snapshotsOpen])

  const handleScopeChange = useCallback(
    (nextScope: GraphScope) => {
      if (nextScope === scope) return
      setScope(nextScope)
      setSnapshot(null)
      setMissing(false)
      setError(null)
      setQuery("")
      setSelectedCategoryId(null)
      setSelectedNodeId(null)
      setCategoriesOpen(false)
      setSnapshotsOpen(false)
      setDesde("")
      setHasta("")
      setDateResults(null)
      setIndexStatus(null)
    },
    [scope]
  )

  const handleSelectCategory = useCallback((categoryId: string) => {
    setSelectedCategoryId(categoryId)
    setSelectedNodeId(categoryId)
    setCategoriesOpen(false)
  }, [])

  const handleSelectChild = useCallback(
    (childId: string) => {
      const parent = index.find((category) =>
        category.children.some((child) => child.id === childId)
      )
      if (!parent) return
      setSelectedCategoryId(parent.id)
      setSelectedNodeId(childId)
      setCategoriesOpen(false)
    },
    [index]
  )

  const handleSelectNode = useCallback(
    (node: GraphNode) => {
      if (node.kind === "n1") {
        const isSameCategory = selectedCategoryId === node.id
        setSelectedCategoryId(isSameCategory ? null : node.id)
        setSelectedNodeId(isSameCategory ? null : node.id)
        return
      }
      setSelectedCategoryId(node.categoryId)
      setSelectedNodeId(node.id)
    },
    [selectedCategoryId]
  )

  const handleClearNode = useCallback(() => {
    setSelectedNodeId(null)
  }, [])

  const handleShowCategories = useCallback(() => {
    setSelectedNodeId(null)
    if (window.matchMedia("(max-width: 1279px)").matches) {
      setCategoriesOpen(true)
    }
  }, [])

  const handleSelectSnapshot = useCallback(
    async (id: string): Promise<boolean> => {
      setHistLoading(true)
      setError(null)
      try {
        const data = await obtenerGrafoPorId(id)
        setSnapshot(data)
        setMissing(false)
        setSelectedCategoryId(null)
        setSelectedNodeId(null)
        return true
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "No se pudo abrir ese snapshot."
        )
        return false
      } finally {
        setHistLoading(false)
      }
    },
    []
  )

  const handleSearchRange = useCallback(async () => {
    if (!desde || !hasta) return
    setHistLoading(true)
    setError(null)
    try {
      setDateResults(await buscarGrafosPorFecha(desde, hasta))
    } catch (err) {
      setDateResults([])
      setError(
        err instanceof Error
          ? err.message
          : "No se pudo buscar snapshots por fecha."
      )
    } finally {
      setHistLoading(false)
    }
  }, [desde, hasta])

  const empty =
    !loading && (missing || !snapshot || index.length === 0)
  const showTopError = Boolean(error && (!snapshotsOpen || scope === "PRIVATE"))

  return (
    <AuthGate>
      <AppShell
        currentPath="/grafo"
        contentClassName="max-w-[1600px] px-3 py-4 sm:px-5 xl:px-6"
      >
        <div className={styles.observatory}>
          <header className={styles.workspaceHeader}>
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <p className={styles.workspaceKicker}>Observatorio · GRF-01</p>
                <h1 className="mt-1 text-2xl font-bold text-institutional sm:text-3xl">
                  Observatorio GraphRAG
                </h1>
                <p className="mt-1 max-w-3xl text-sm leading-relaxed text-foreground">
                  Explora categorías, subnodos y relaciones del conocimiento
                  institucional sin perder el documento que las respalda.
                </p>
              </div>
              <p className="max-w-xs font-mono text-[10px] leading-relaxed text-muted-foreground">
                Campo cartográfico · N1/N2 visibles · relaciones N3 en
                inspector
              </p>
            </div>
          </header>

          <section className={styles.scopeBar} aria-label="Estado del observatorio">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div
                className="flex border-2 border-institutional"
                role="group"
                aria-label="Ámbito del grafo"
              >
                <button
                  type="button"
                  aria-pressed={scope === "BASE"}
                  onClick={() => handleScopeChange("BASE")}
                  className={`px-3 py-2 text-xs font-bold ${scope === "BASE" ? "bg-institutional text-primary-foreground" : "bg-card text-institutional"}`}
                >
                  Corpus base
                </button>
                <button
                  type="button"
                  aria-pressed={scope === "PRIVATE"}
                  onClick={() => handleScopeChange("PRIVATE")}
                  className={`border-l-2 border-institutional px-3 py-2 text-xs font-bold ${scope === "PRIVATE" ? "bg-institutional text-primary-foreground" : "bg-card text-institutional"}`}
                >
                  Mi corpus
                </button>
              </div>

              <div className="flex flex-wrap items-center justify-end gap-2">
                {snapshot ? (
                  <span className="font-mono text-[10px] text-muted-foreground">
                    {scope === "PRIVATE"
                      ? `Release ${snapshot.releaseId?.slice(0, 8) ?? "privado"}`
                      : `Snapshot ${snapshot.id.slice(0, 8)}`}{" "}
                    · {formatSnapshotDate(snapshot)}
                  </span>
                ) : (
                  <span className="font-mono text-[10px] text-muted-foreground">
                    Sin publicación visible
                  </span>
                )}
                {scope === "BASE" ? (
                  <button
                    ref={snapshotTriggerRef}
                    type="button"
                    onClick={() => setSnapshotsOpen(true)}
                    className="border-2 border-institutional bg-card px-3 py-2 text-xs font-bold text-institutional"
                  >
                    Snapshots
                  </button>
                ) : null}
                <button
                  ref={exploreTriggerRef}
                  type="button"
                  onClick={() => setCategoriesOpen(true)}
                  className="border-2 border-sst-yellow bg-sst-yellow px-3 py-2 text-xs font-bold text-institutional xl:hidden"
                >
                  Explorar
                </button>
              </div>
            </div>

            <div className={`${styles.statsStrip} mt-4`}>
              <Stat label="Categorías N1" value={stats.categories} />
              <Stat label="Subnodos N2" value={stats.subcategories} />
              <Stat label="Relaciones N3" value={stats.relations} />
              <Stat label="Documentos únicos" value={stats.documents} />
            </div>

            {scope === "PRIVATE" && indexStatus ? (
              <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-border/70 pt-3">
                {isActiveIndex(indexStatus) ? (
                  <span className="font-mono text-[10px] font-bold text-institutional">
                    Actualizando · {indexStatus.etapa ?? "reconstrucción"}
                  </span>
                ) : (
                  <span className="font-mono text-[10px] font-bold text-institutional">
                    Índice · {indexStatus.estado}
                  </span>
                )}
                {indexStatus.estado === "FAILED" ? (
                  <>
                    <span className="text-xs text-stamp-red">
                      {indexStatus.mensaje ?? "La actualización del índice falló."}
                    </span>
                    <Link
                      href="/archivos"
                      className="font-semibold text-stamp-red underline underline-offset-2"
                    >
                      Gestionar archivos
                    </Link>
                  </>
                ) : null}
                {snapshot?.generation != null ? (
                  <span className="font-mono text-[10px] text-muted-foreground">
                    Generación {snapshot.generation}
                  </span>
                ) : null}
              </div>
            ) : null}
          </section>

          {showTopError ? (
            <FormAlert variant="error" className="mt-4 flex flex-wrap items-center justify-between gap-3">
              <span>{error}</span>
              <button
                type="button"
                onClick={() => void loadActual(scope)}
                className="border border-stamp-red px-3 py-1.5 text-xs font-bold"
              >
                Reintentar
              </button>
            </FormAlert>
          ) : null}

          <div className="mt-4">
            {loading && !snapshot ? (
              <ObservatorySkeleton />
            ) : empty ? (
              <EmptyGraphState scope={scope} onRetry={() => void loadActual(scope)} />
            ) : (
              <div className="grid min-w-0 gap-3 xl:grid-cols-[18rem_minmax(0,1fr)_21rem]">
                <div className="hidden min-w-0 xl:block">
                  <GraphCategoryNavigator
                    index={index}
                    filteredIndex={filteredIndex}
                    query={query}
                    selectedCategoryId={selectedCategoryId}
                    selectedNodeId={selectedNodeId}
                    onQueryChange={setQuery}
                    onSelectCategory={handleSelectCategory}
                    onSelectChild={handleSelectChild}
                  />
                </div>

                <section className="min-w-0" aria-labelledby="graph-canvas-heading">
                  <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
                    <div>
                      <p className={styles.workspaceKicker}>Campo cartográfico</p>
                      <h2 id="graph-canvas-heading" className="mt-1 text-base font-bold text-institutional">
                        Relaciones de pertenencia
                      </h2>
                    </div>
                    <p className="font-mono text-[10px] text-muted-foreground">
                      {selectedCategory
                        ? `${selectedCategory.title} · ${selectedCategory.childCount} N2`
                        : "Selecciona una baliza N1"}
                    </p>
                  </div>
                  <div className="h-[58svh] min-h-[420px] xl:h-[calc(100svh-13rem)] xl:min-h-[620px]">
                    <GraphObservatoryCanvas
                      data={graph}
                      selectedNodeId={selectedNodeId}
                      selectedCategoryId={selectedCategoryId}
                      reduceMotion={reduceMotion}
                      onSelectNode={handleSelectNode}
                      onClearNode={handleClearNode}
                      onShowCategories={handleShowCategories}
                    />
                  </div>
                </section>

                <div className="hidden min-w-0 xl:block">
                  <GraphInspector
                    stats={stats}
                    category={selectedCategory}
                    child={selectedChild}
                    onSelectChild={handleSelectChild}
                  />
                </div>

                <div className="min-w-0 xl:hidden">
                  <GraphInspector
                    stats={stats}
                    category={selectedCategory}
                    child={selectedChild}
                    onSelectChild={handleSelectChild}
                  />
                </div>
              </div>
            )}
          </div>

          <GraphDrawer
            open={categoriesOpen}
            side="left"
            title="Explorar categorías"
            triggerRef={exploreTriggerRef}
            onClose={() => setCategoriesOpen(false)}
          >
            <GraphCategoryNavigator
              index={index}
              filteredIndex={filteredIndex}
              query={query}
              selectedCategoryId={selectedCategoryId}
              selectedNodeId={selectedNodeId}
              onQueryChange={setQuery}
              onSelectCategory={handleSelectCategory}
              onSelectChild={handleSelectChild}
            />
          </GraphDrawer>

          {scope === "BASE" ? (
            <GraphSnapshotDrawer
              open={snapshotsOpen}
              triggerRef={snapshotTriggerRef}
              snapshots={historial}
              currentId={snapshot?.id ?? null}
              page={histPage}
              totalPages={histTotalPages}
              desde={desde}
              hasta={hasta}
              dateResults={dateResults}
              loading={histLoading}
              error={snapshotsOpen ? error : null}
              onClose={() => setSnapshotsOpen(false)}
              onPageChange={(page) => void loadHistorial(page)}
              onRangeChange={(field, value) => {
                if (field === "desde") setDesde(value)
                else setHasta(value)
              }}
              onSearchRange={() => void handleSearchRange()}
              onSelectSnapshot={handleSelectSnapshot}
            />
          ) : null}
        </div>
      </AppShell>
    </AuthGate>
  )
}
