"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { Download, RefreshCw, Trash2, Upload } from "lucide-react"

import { AuthGate } from "@/components/auth/auth-gate"
import { AppShell } from "@/components/clipboard/app-shell"
import { FormPaper } from "@/components/clipboard/form-elements"
import { FormAlert } from "@/components/clipboard/form-field"
import { formatBytes, formatFileType } from "@/lib/format"
import { descargarArchivo, eliminarArchivo, listarArchivos, subirArchivo } from "@/services/archivo.service"
import { obtenerIndice, reintentarIndice } from "@/services/indice.service"
import type { ArchivoDominio, ArchivoResponse, ArchivoTipoFiltro } from "@/types/archivo.types"
import type { IndiceEstado } from "@/types/indice.types"

const PAGE_SIZE = 20
const MAX_QUEUE = 5

type UploadItem = {
  id: string
  file: File
  dominio: ArchivoDominio | ""
  progress: number
  status: "QUEUED" | "UPLOADING" | "DONE" | "FAILED"
  error?: string
}

function itemId(file: File): string {
  return `${file.name}-${file.size}-${file.lastModified}`
}

function isActiveIndex(status?: IndiceEstado | null): boolean {
  return status?.estado === "DIRTY" || status?.estado === "QUEUED" || status?.estado === "RUNNING"
}

export function ArchivosPanel() {
  const [files, setFiles] = useState<ArchivoResponse[]>([])
  const [queue, setQueue] = useState<UploadItem[]>([])
  const [page, setPage] = useState(0)
  const [totalPages, setTotalPages] = useState(0)
  const [totalElements, setTotalElements] = useState(0)
  const [q, setQ] = useState("")
  const [tipo, setTipo] = useState<ArchivoTipoFiltro>("")
  const [indexStatus, setIndexStatus] = useState<IndiceEstado | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [fileInputKey, setFileInputKey] = useState(0)

  async function loadPage(nextPage = page, nextQ = q, nextTipo = tipo) {
    setLoading(true)
    try {
      const data = await listarArchivos({ page: nextPage, size: PAGE_SIZE, q: nextQ, tipo: nextTipo })
      setFiles(data.items)
      setPage(data.page)
      setTotalPages(data.totalPages)
      setTotalElements(data.totalElements)
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cargar el repositorio.")
    } finally {
      setLoading(false)
    }
  }

  async function loadIndexStatus() {
    try {
      setIndexStatus(await obtenerIndice())
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo consultar el estado de indexación.")
    }
  }

  useEffect(() => {
    void loadPage(0, "", "")
    void loadIndexStatus()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!isActiveIndex(indexStatus)) return
    const timer = window.setInterval(() => void loadIndexStatus(), 5000)
    return () => window.clearInterval(timer)
  }, [indexStatus])

  function addFiles(selected: FileList | File[]) {
    const room = MAX_QUEUE - queue.length
    if (room <= 0) {
      setError(`Máximo ${MAX_QUEUE} archivos por cola.`)
      return
    }
    const next = Array.from(selected).slice(0, room).map((file) => ({
      id: itemId(file),
      file,
      dominio: "" as const,
      progress: 0,
      status: "QUEUED" as const,
    }))
    setQueue((current) => [...current, ...next])
    setError(null)
    setFileInputKey((value) => value + 1)
  }

  function setDomain(id: string, dominio: ArchivoDominio) {
    setQueue((current) => current.map((item) => item.id === id ? { ...item, dominio, error: undefined } : item))
  }

  async function uploadQueue() {
    const pending = queue.filter((item) => item.status === "QUEUED")
    if (pending.some((item) => !item.dominio)) {
      setError("Selecciona ISOS o LEYES para cada archivo antes de subir.")
      return
    }
    setError(null)
    for (const item of pending) {
      setQueue((current) => current.map((row) => row.id === item.id ? { ...row, status: "UPLOADING", progress: 15 } : row))
      try {
        await subirArchivo(item.file, item.dominio as ArchivoDominio)
        setQueue((current) => current.map((row) => row.id === item.id ? { ...row, status: "DONE", progress: 100 } : row))
      } catch (err) {
        setQueue((current) => current.map((row) => row.id === item.id ? { ...row, status: "FAILED", error: err instanceof Error ? err.message : "No se pudo subir el archivo." } : row))
      }
    }
    setMessage("Archivos recibidos. La reconstrucción del índice continuará en segundo plano.")
    await Promise.all([loadPage(0, q, tipo), loadIndexStatus()])
  }

  async function retryIndex() {
    try {
      setIndexStatus(await reintentarIndice())
      setMessage("Reintento solicitado.")
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo reintentar la indexación.")
    }
  }

  async function deleteFile(file: ArchivoResponse) {
    if (!window.confirm(`¿Eliminar «${file.nombre}» y reconstruir el índice privado?`)) return
    setDeletingId(file.id)
    try {
      await eliminarArchivo(file.id)
      setFiles((current) => current.map((row) => row.id === file.id ? { ...row, pendienteEliminacion: true } : row))
      setMessage(`${file.nombre} quedó pendiente hasta completar la reconstrucción.`)
      await loadIndexStatus()
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo solicitar la eliminación.")
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <AuthGate>
      <AppShell currentPath="/archivos">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">Form. REP-01</p>
            <h1 className="text-2xl font-bold text-institutional sm:text-3xl">Archivos privados</h1>
            <p className="mt-1 max-w-2xl text-sm text-muted-foreground">Sube hasta {MAX_QUEUE} PDF, TXT o MD. Data Science procesa el original dentro del índice privado; el navegador nunca extrae texto.</p>
          </div>
          <Link href="/consultar" className="font-semibold text-carbon hover:underline">Ir a Consultar</Link>
        </div>
        {error ? <FormAlert variant="error" className="mb-4">{error}</FormAlert> : null}
        {message ? <FormAlert variant="info" className="mb-4">{message}</FormAlert> : null}

        <div className="mb-6 grid gap-4 lg:grid-cols-[1fr_20rem]">
          <FormPaper className="p-5 sm:p-6">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-bold text-institutional">Cola de carga</h2>
                <p className="text-xs text-muted-foreground">{queue.length}/{MAX_QUEUE} archivos</p>
              </div>
              <label className="inline-flex cursor-pointer items-center gap-2 border-2 border-institutional bg-sst-yellow px-3 py-2 text-xs font-bold text-institutional">
                <Upload className="size-4" aria-hidden />
                Agregar
                <input key={fileInputKey} type="file" multiple accept=".pdf,.txt,.md,application/pdf,text/plain,text/markdown" className="hidden" onChange={(event) => event.target.files && addFiles(event.target.files)} />
              </label>
            </div>
            {queue.length === 0 ? <p className="border border-dashed border-border p-5 text-sm text-muted-foreground">Agrega archivos para construir tu corpus privado.</p> : (
              <ul className="space-y-3">
                {queue.map((item) => (
                  <li key={item.id} className="border border-border p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-institutional">{item.file.name}</p>
                        <p className="font-mono text-[10px] text-muted-foreground">{formatBytes(item.file.size)} · {item.status}</p>
                      </div>
                      <select value={item.dominio} onChange={(event) => setDomain(item.id, event.target.value as ArchivoDominio)} disabled={item.status !== "QUEUED"} required className="border border-border bg-paper px-2 py-1 text-xs">
                        <option value="">Dominio…</option>
                        <option value="ISOS">ISOS</option>
                        <option value="LEYES">LEYES</option>
                      </select>
                    </div>
                    {item.status === "UPLOADING" || item.status === "DONE" ? <div className="mt-2 h-1.5 bg-muted"><div className="h-full bg-institutional transition-all" style={{ width: `${item.progress}%` }} /></div> : null}
                    {item.error ? <p className="mt-2 text-xs text-stamp-red">{item.error}</p> : null}
                  </li>
                ))}
              </ul>
            )}
            <button type="button" onClick={() => void uploadQueue()} disabled={!queue.some((item) => item.status === "QUEUED")} className="mt-4 inline-flex items-center gap-2 border-2 border-institutional px-4 py-2 text-sm font-bold text-institutional disabled:opacity-50">
              <Upload className="size-4" aria-hidden /> Subir y reconstruir índice
            </button>
          </FormPaper>

          <FormPaper className="p-5 sm:p-6">
            <div className="mb-3 flex items-center justify-between gap-2"><h2 className="text-lg font-bold text-institutional">Estado del índice</h2><RefreshCw className="size-4 text-muted-foreground" aria-hidden /></div>
            <p className="font-mono text-sm font-bold text-institutional">{indexStatus?.estado ?? "Cargando…"}</p>
            {indexStatus?.etapa ? <p className="mt-1 font-mono text-[10px] uppercase text-muted-foreground">Etapa: {indexStatus.etapa}</p> : null}
            {indexStatus?.mensaje ? <p className="mt-3 text-xs leading-relaxed text-muted-foreground">{indexStatus.mensaje}</p> : null}
            {indexStatus?.release_id ? <p className="mt-3 font-mono text-[10px] text-muted-foreground">Release activo: {indexStatus.release_id.slice(0, 8)}</p> : null}
            {indexStatus?.estado === "FAILED" ? <button type="button" onClick={() => void retryIndex()} className="mt-4 inline-flex items-center gap-2 border-2 border-stamp-red/50 px-3 py-1.5 text-xs font-semibold text-stamp-red"><RefreshCw className="size-3.5" aria-hidden /> Reintentar</button> : null}
            {isActiveIndex(indexStatus) && indexStatus?.release_id ? <p className="mt-4 border-t border-border pt-3 text-xs text-muted-foreground">El grafo visible sigue siendo el último release exitoso durante la reconstrucción.</p> : null}
          </FormPaper>
        </div>

        <form onSubmit={(event) => { event.preventDefault(); void loadPage(0, q, tipo) }} className="mb-5 flex flex-wrap items-end gap-3">
          <label className="flex min-w-[12rem] flex-1 flex-col gap-1"><span className="font-mono text-[10px] font-bold uppercase text-institutional">Buscar archivo</span><input value={q} onChange={(event) => setQ(event.target.value)} className="border-2 border-border bg-paper px-3 py-2 text-sm" placeholder="Nombre…" /></label>
          <label className="flex flex-col gap-1"><span className="font-mono text-[10px] font-bold uppercase text-institutional">Tipo</span><select value={tipo} onChange={(event) => setTipo(event.target.value as ArchivoTipoFiltro)} className="border-2 border-border bg-paper px-3 py-2 text-sm"><option value="">Todos</option><option value="pdf">PDF</option><option value="txt">TXT</option><option value="md">MD</option></select></label>
          <button type="submit" className="border-2 border-institutional bg-card px-4 py-2 text-sm font-semibold text-institutional">Filtrar</button>
        </form>

        <section aria-labelledby="files-list-heading">
          <h2 id="files-list-heading" className="mb-4 text-lg font-bold text-institutional">Archivos almacenados <span className="ml-2 font-mono text-xs font-normal text-muted-foreground">{totalElements} en total</span></h2>
          {loading ? <p className="font-mono text-sm text-muted-foreground">Cargando repositorio…</p> : files.length === 0 ? <FormPaper className="p-8 text-center"><p className="mb-2 font-semibold text-institutional">Repositorio vacío</p><p className="mb-4 text-sm text-muted-foreground">Sube un archivo para crear tu primer overlay privado.</p></FormPaper> : (
            <>
              <div className="overflow-x-auto border-2 border-institutional"><table className="w-full min-w-[760px] text-left text-sm"><thead className="border-b-2 border-institutional bg-muted"><tr>{["Nombre", "Dominio", "Tipo", "Tamaño", "Indexado", "Acciones"].map((heading) => <th key={heading} className="px-4 py-3 font-mono text-[10px] font-bold uppercase tracking-wider text-institutional">{heading}</th>)}</tr></thead><tbody>{files.map((file) => <tr key={file.id} className={`border-b border-border last:border-b-0 ${file.pendienteEliminacion ? "bg-stamp-red/5" : "bg-card"}`}><td className="max-w-[220px] truncate px-4 py-3 font-medium text-institutional">{file.nombre}{file.pendienteEliminacion ? <span className="ml-2 text-[10px] font-semibold text-stamp-red">pendiente</span> : null}</td><td className="px-4 py-3 font-mono text-xs text-muted-foreground">{file.dominio ?? "Legado"}</td><td className="px-4 py-3 font-mono text-xs text-muted-foreground">{formatFileType(file.tipo)}</td><td className="px-4 py-3 font-mono text-xs text-muted-foreground">{formatBytes(file.tamano)}</td><td className="px-4 py-3 font-mono text-[10px] text-muted-foreground">{file.indexadoEn ? new Date(file.indexadoEn).toLocaleString("es-CL") : "Pendiente"}</td><td className="px-4 py-3"><div className="flex flex-wrap gap-2"><button type="button" onClick={() => void descargarArchivo(file.id, file.nombre)} className="inline-flex items-center gap-1 border border-border px-2 py-1 text-xs font-semibold text-institutional hover:bg-muted"><Download className="size-3.5" aria-hidden /> Descargar</button><button type="button" disabled={deletingId === file.id || file.pendienteEliminacion} onClick={() => void deleteFile(file)} className="inline-flex items-center gap-1 border border-stamp-red/40 px-2 py-1 text-xs font-semibold text-stamp-red disabled:opacity-50"><Trash2 className="size-3.5" aria-hidden /> Eliminar y reconstruir</button></div></td></tr>)}</tbody></table></div>
              {totalPages > 1 ? <div className="mt-3 flex items-center justify-between font-mono text-xs text-muted-foreground"><button type="button" disabled={page <= 0} onClick={() => void loadPage(page - 1, q, tipo)} className="border border-border px-2 py-1 disabled:opacity-40">Anterior</button><span>Página {page + 1} de {totalPages}</span><button type="button" disabled={page + 1 >= totalPages} onClick={() => void loadPage(page + 1, q, tipo)} className="border border-border px-2 py-1 disabled:opacity-40">Siguiente</button></div> : null}
            </>
          )}
        </section>
      </AppShell>
    </AuthGate>
  )
}
