"use client"

import type { ChangeEvent, FormEvent, RefObject } from "react"

import { GraphDrawer } from "@/components/grafo/graph-drawer"
import type { GrafoResponse } from "@/types/grafo.types"

export interface GraphSnapshotDrawerProps {
  open: boolean
  triggerRef: RefObject<HTMLElement | null>
  snapshots: GrafoResponse[]
  currentId: string | null
  page: number
  totalPages: number
  desde: string
  hasta: string
  dateResults: GrafoResponse[] | null
  loading: boolean
  error: string | null
  onClose: () => void
  onPageChange: (page: number) => void
  onRangeChange: (field: "desde" | "hasta", value: string) => void
  onSearchRange: () => void
  onSelectSnapshot: (id: string) => void | Promise<boolean>
}

function snapshotDate(snapshot: GrafoResponse): string {
  return snapshot.fechaCreacion
    ? new Date(snapshot.fechaCreacion).toLocaleDateString("es-CL", {
        day: "numeric",
        month: "long",
        year: "numeric",
      })
    : "Sin fecha registrada"
}

function SnapshotButton({
  snapshot,
  current,
  onSelect,
}: {
  snapshot: GrafoResponse
  current: boolean
  onSelect: () => void
}) {
  return (
    <li>
      <button
        type="button"
        aria-current={current ? "true" : undefined}
        onClick={onSelect}
        className={`w-full border px-3 py-2 text-left transition-colors hover:border-institutional hover:bg-sst-yellow/15 focus-visible:bg-sst-yellow/15 ${current ? "border-institutional bg-sst-yellow/20" : "border-border"}`}
      >
        <span className="block text-xs font-semibold text-institutional">
          {snapshotDate(snapshot)}
        </span>
        {current ? (
          <span className="mt-1 block font-mono text-[10px] text-stamp-red">
            Versión actual
          </span>
        ) : null}
      </button>
    </li>
  )
}

export function GraphSnapshotDrawer({
  open,
  triggerRef,
  snapshots,
  currentId,
  page,
  totalPages,
  desde,
  hasta,
  dateResults,
  loading,
  error,
  onClose,
  onPageChange,
  onRangeChange,
  onSearchRange,
  onSelectSnapshot,
}: GraphSnapshotDrawerProps) {
  function handleRangeChange(
    event: ChangeEvent<HTMLInputElement>,
    field: "desde" | "hasta"
  ) {
    onRangeChange(field, event.target.value)
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    onSearchRange()
  }

  async function selectSnapshot(id: string) {
    const loaded = await onSelectSnapshot(id)
    if (loaded !== false) onClose()
  }

  return (
    <GraphDrawer
      open={open}
      side="right"
      title="Versiones de la biblioteca general"
      triggerRef={triggerRef}
      onClose={onClose}
    >
      <div className="space-y-5">
        {error ? (
          <p role="alert" className="border-2 border-stamp-red p-3 text-xs text-stamp-red">
            {error}
          </p>
        ) : null}

        <section aria-labelledby="snapshot-history-heading">
          <div className="flex items-end justify-between gap-2">
            <div>
              <p className="font-mono text-[10px] font-bold uppercase tracking-wider text-institutional">
                Historial de versiones
              </p>
              <h3 id="snapshot-history-heading" className="mt-1 text-sm font-bold text-institutional">
                Versiones publicadas
              </h3>
            </div>
            {loading ? (
              <span className="font-mono text-[10px] text-muted-foreground">Cargando…</span>
            ) : null}
          </div>

          {snapshots.length === 0 && !loading ? (
            <p className="mt-3 border border-dashed border-border p-3 text-xs text-muted-foreground">
              Sin versiones publicadas
            </p>
          ) : (
            <ul className="mt-3 space-y-2">
              {snapshots.slice(0, 8).map((snapshot) => (
                <SnapshotButton
                  key={snapshot.id}
                  snapshot={snapshot}
                  current={snapshot.id === currentId}
                  onSelect={() => selectSnapshot(snapshot.id)}
                />
              ))}
            </ul>
          )}

          {totalPages > 1 ? (
            <div className="mt-3 flex items-center justify-between gap-2 border-t border-border pt-3 font-mono text-[10px] text-muted-foreground">
              <button
                type="button"
                disabled={page <= 0 || loading}
                onClick={() => onPageChange(page - 1)}
                className="border border-border px-2 py-1 disabled:opacity-40"
              >
                Anterior
              </button>
              <span>
                Página {page + 1} de {totalPages}
              </span>
              <button
                type="button"
                disabled={page + 1 >= totalPages || loading}
                onClick={() => onPageChange(page + 1)}
                className="border border-border px-2 py-1 disabled:opacity-40"
              >
                Siguiente
              </button>
            </div>
          ) : null}
        </section>

        <section aria-labelledby="snapshot-date-heading" className="border-t border-border pt-4">
          <p className="font-mono text-[10px] font-bold uppercase tracking-wider text-institutional">
            Buscar por fecha
          </p>
          <h3 id="snapshot-date-heading" className="mt-1 text-sm font-bold text-institutional">
            Rango del registro
          </h3>
          <form onSubmit={handleSubmit} className="mt-3 space-y-2">
            <label className="block text-xs text-foreground">
              Desde
              <input
                type="date"
                value={desde}
                onChange={(event) => handleRangeChange(event, "desde")}
                className="mt-1 w-full border-2 border-border bg-card px-2 py-1.5 text-sm"
                required
              />
            </label>
            <label className="block text-xs text-foreground">
              Hasta
              <input
                type="date"
                value={hasta}
                onChange={(event) => handleRangeChange(event, "hasta")}
                className="mt-1 w-full border-2 border-border bg-card px-2 py-1.5 text-sm"
                required
              />
            </label>
            <button
              type="submit"
              className="w-full border-2 border-institutional bg-card px-3 py-2 text-xs font-bold text-institutional"
            >
              Buscar rango
            </button>
          </form>
          {dateResults ? (
            dateResults.length === 0 ? (
              <p className="mt-3 border border-dashed border-border p-3 text-xs text-muted-foreground">
                No hay versiones en ese rango
              </p>
            ) : (
              <ul className="mt-3 space-y-2">
                {dateResults.map((snapshot) => (
                  <SnapshotButton
                    key={snapshot.id}
                    snapshot={snapshot}
                    current={snapshot.id === currentId}
                    onSelect={() => selectSnapshot(snapshot.id)}
                  />
                ))}
              </ul>
            )
          ) : null}
        </section>
      </div>
    </GraphDrawer>
  )
}
