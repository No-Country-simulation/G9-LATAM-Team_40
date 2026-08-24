import { apiFetch } from "@/lib/api"
import type { IndiceEstado } from "@/types/indice.types"

export async function obtenerIndice(): Promise<IndiceEstado> {
  return apiFetch<IndiceEstado>("/api/indice")
}

export async function reintentarIndice(): Promise<IndiceEstado> {
  return apiFetch<IndiceEstado>("/api/indice/reintentar", { method: "POST" })
}
