import { apiFetch } from "@/lib/api"
import { mapConsulta, mapConsultaList } from "@/lib/api-mappers"
import type { ConsultaRequest, ConsultaResponse } from "@/types/consulta.types"

export async function analizarConsulta(data: ConsultaRequest): Promise<ConsultaResponse> {
  const raw = await apiFetch<unknown>("/api/consultas", {
    method: "POST",
    body: JSON.stringify(data),
  })
  return mapConsulta(raw)
}

export async function obtenerConsulta(id: string): Promise<ConsultaResponse> {
  return mapConsulta(await apiFetch<unknown>(`/api/consultas/${encodeURIComponent(id)}`, { method: "GET" }))
}

export async function listarConsultas(): Promise<ConsultaResponse[]> {
  return mapConsultaList(await apiFetch<unknown>("/api/consultas"))
}

export async function buscarConsultas(q: string): Promise<ConsultaResponse[]> {
  const query = q.trim()
  if (!query) return []
  return mapConsultaList(await apiFetch<unknown>(`/api/consultas/buscar?q=${encodeURIComponent(query)}`))
}
