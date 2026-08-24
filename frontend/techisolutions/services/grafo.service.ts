import { apiFetch } from "@/lib/api"
import { mapGrafo, mapGrafoList, mapSpringPageGrafos } from "@/lib/api-mappers"
import type { GrafoResponse, SpringPage } from "@/types/grafo.types"

export async function obtenerGrafoActual(): Promise<GrafoResponse> {
  return mapGrafo(await apiFetch<unknown>("/api/grafos/actual"))
}

export async function obtenerGrafoPrivado(): Promise<GrafoResponse> {
  return mapGrafo(await apiFetch<unknown>("/api/grafos/privado"))
}

export async function obtenerGrafoPorId(id: string): Promise<GrafoResponse> {
  return mapGrafo(await apiFetch<unknown>(`/api/grafos/id/${id}`))
}

export async function listarHistorialGrafos(page = 0, size = 10): Promise<SpringPage<GrafoResponse>> {
  const search = new URLSearchParams({ page: String(page), size: String(size) })
  return mapSpringPageGrafos(await apiFetch<unknown>(`/api/grafos/historial?${search}`))
}

export async function buscarGrafosPorFecha(desde: string, hasta: string): Promise<GrafoResponse[]> {
  const search = new URLSearchParams({ desde, hasta })
  return mapGrafoList(await apiFetch<unknown>(`/api/grafos/buscarfecha?${search}`))
}

export async function sincronizarGrafo(objectName?: string): Promise<GrafoResponse> {
  const search = objectName?.trim() ? `?objectName=${encodeURIComponent(objectName.trim())}` : ""
  return mapGrafo(await apiFetch<unknown>(`/api/grafos/sincronizar${search}`, { method: "POST" }))
}
