import { apiFetch, apiFetchBlob } from "@/lib/api"
import { mapArchivo, mapArchivoPagina } from "@/lib/api-mappers"
import type {
  ArchivoDominio,
  ArchivoResponse,
  ArchivoTipoFiltro,
  PaginaResponse,
} from "@/types/archivo.types"

export type ListarArchivosParams = {
  page?: number
  size?: number
  q?: string
  tipo?: ArchivoTipoFiltro
}

export async function listarArchivos(
  params: ListarArchivosParams = {}
): Promise<PaginaResponse<ArchivoResponse>> {
  const search = new URLSearchParams({
    page: String(params.page ?? 0),
    size: String(params.size ?? 20),
    q: params.q?.trim() ?? "",
    tipo: params.tipo ?? "",
  })
  return mapArchivoPagina(await apiFetch<unknown>(`/api/archivos?${search.toString()}`))
}

export async function subirArchivo(file: File, dominio: ArchivoDominio): Promise<ArchivoResponse> {
  const formData = new FormData()
  formData.append("file", file)
  formData.append("dominio", dominio)
  return mapArchivo(await apiFetch<unknown>("/api/archivos", { method: "POST", body: formData }))
}

export async function obtenerArchivo(id: string): Promise<ArchivoResponse> {
  return mapArchivo(await apiFetch<unknown>(`/api/archivos/${id}`))
}

export async function eliminarArchivo(id: string): Promise<void> {
  await apiFetch<void>(`/api/archivos/${id}`, { method: "DELETE" })
}

export async function descargarArchivo(id: string, nombre: string): Promise<void> {
  const blob = await apiFetchBlob(`/api/archivos/${encodeURIComponent(id)}/descarga`)
  const objectUrl = URL.createObjectURL(blob)
  const anchor = document.createElement("a")
  anchor.href = objectUrl
  anchor.download = nombre
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 0)
}
