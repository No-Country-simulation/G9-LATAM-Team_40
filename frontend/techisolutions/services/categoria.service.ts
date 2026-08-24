import { apiFetch } from "@/lib/api"
import { mapCategoriaList } from "@/lib/api-mappers"
import type { CategoriaResponse } from "@/types/categoria.types"

export async function listarCategorias(): Promise<CategoriaResponse[]> {
  return mapCategoriaList(await apiFetch<unknown>("/api/categorias"))
}
