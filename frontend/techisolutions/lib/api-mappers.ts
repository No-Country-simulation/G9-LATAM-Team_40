import type { ArchivoResponse, PaginaResponse } from "@/types/archivo.types"
import type { CategoriaResponse } from "@/types/categoria.types"
import type { ConsultaResponse, TrazabilidadSeccion } from "@/types/consulta.types"
import type { GrafoJsonData, GrafoResponse, SpringPage } from "@/types/grafo.types"

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object" ? (value as Record<string, unknown>) : {}
}

function asString(value: unknown, fallback = ""): string {
  if (typeof value === "string") return value
  if (value == null) return fallback
  return String(value)
}

function asNumber(value: unknown, fallback = 0): number {
  if (typeof value === "number" && Number.isFinite(value)) return value
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value)
    if (Number.isFinite(parsed)) return parsed
  }
  return fallback
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return []
  return value.map((item) => asString(item)).filter(Boolean)
}

function pick(obj: Record<string, unknown>, ...keys: string[]): unknown {
  for (const key of keys) {
    if (obj[key] !== undefined && obj[key] !== null) return obj[key]
  }
  return undefined
}

function mapTrace(raw: unknown): TrazabilidadSeccion {
  const obj = asRecord(raw)
  const corpus = asString(pick(obj, "corpus"), "BASE").toUpperCase()
  return {
    documentoId: asString(pick(obj, "documento_id", "documentoId")),
    documentoTitulo: asString(pick(obj, "documento_titulo", "documentoTitulo")),
    categoria: asString(pick(obj, "categoria"), "Sin Categoría"),
    palabrasClave: asStringArray(pick(obj, "palabras_clave", "palabrasClave")),
    tituloSeccion: asString(pick(obj, "titulo_seccion", "tituloSeccion")),
    rutaJerarquica: asStringArray(pick(obj, "ruta_jerarquica", "rutaJerarquica")),
    nivel: asNumber(pick(obj, "nivel"), 1),
    dominio: asString(pick(obj, "dominio")),
    relevancia: asNumber(pick(obj, "relevancia", "score")),
    corpus: corpus === "PRIVADO" ? "PRIVADO" : "BASE",
    archivoId: pick(obj, "archivo_id", "archivoId") ? asString(pick(obj, "archivo_id", "archivoId")) : undefined,
  }
}

export function mapConsulta(raw: unknown): ConsultaResponse {
  const obj = asRecord(raw)
  const trace = pick(obj, "trazabilidad")
  return {
    id: asString(pick(obj, "id")),
    pregunta: asString(pick(obj, "pregunta")),
    respuesta: asString(pick(obj, "respuesta")),
    categoriaFuentePrincipal: asString(
      pick(obj, "categoria_fuente_principal", "categoriaFuentePrincipal"),
      "Sin Categoría"
    ),
    relevancia: asNumber(pick(obj, "relevancia")),
    palabrasClave: asStringArray(pick(obj, "palabras_clave", "palabrasClave")),
    trazabilidad: Array.isArray(trace) ? trace.map(mapTrace) : [],
    tiempoSegundos: pick(obj, "tiempo_segundos", "tiempoSegundos") == null
      ? undefined
      : asNumber(pick(obj, "tiempo_segundos", "tiempoSegundos")),
    procesadoEn: asString(pick(obj, "procesado_en", "procesadoEn")),
  }
}

export function mapConsultaList(raw: unknown): ConsultaResponse[] {
  return Array.isArray(raw) ? raw.map(mapConsulta) : []
}

export function mapArchivo(raw: unknown): ArchivoResponse {
  const obj = asRecord(raw)
  const dominio = asString(pick(obj, "dominio"), "")
  return {
    id: asString(pick(obj, "id")),
    nombre: asString(pick(obj, "nombre")),
    documentoId: asString(pick(obj, "documento_id", "documentoId")),
    dominio: dominio === "ISOS" || dominio === "LEYES" ? dominio : undefined,
    tamano: asNumber(pick(obj, "tamano")),
    tipo: asString(pick(obj, "tipo")),
    subidoEn: asString(pick(obj, "subido_en", "subidoEn")),
    indexadoEn: pick(obj, "indexado_en", "indexadoEn") ? asString(pick(obj, "indexado_en", "indexadoEn")) : undefined,
    pendienteEliminacion: Boolean(pick(obj, "pendiente_eliminacion", "pendienteEliminacion")),
  }
}

export function mapArchivoPagina(raw: unknown): PaginaResponse<ArchivoResponse> {
  if (Array.isArray(raw)) {
    return { items: raw.map(mapArchivo), page: 0, size: raw.length, totalElements: raw.length, totalPages: raw.length ? 1 : 0 }
  }
  const obj = asRecord(raw)
  const items = pick(obj, "items", "content")
  return {
    items: Array.isArray(items) ? items.map(mapArchivo) : [],
    page: asNumber(pick(obj, "page", "number")),
    size: asNumber(pick(obj, "size"), 20),
    totalElements: asNumber(pick(obj, "totalElements", "total_elements")),
    totalPages: asNumber(pick(obj, "totalPages", "total_pages")),
  }
}

export function mapCategoria(raw: unknown): CategoriaResponse {
  const obj = asRecord(raw)
  return {
    nombre: asString(pick(obj, "nombre")),
    totalConsultas: asNumber(pick(obj, "total_consultas", "totalConsultas")),
  }
}

export function mapCategoriaList(raw: unknown): CategoriaResponse[] {
  return Array.isArray(raw) ? raw.map(mapCategoria) : []
}

export function mapGrafo(raw: unknown): GrafoResponse {
  const obj = asRecord(raw)
  const jsonData = pick(obj, "json_data", "jsonData")
  const scope = asString(pick(obj, "scope"), "BASE").toUpperCase()
  return {
    id: asString(pick(obj, "id")),
    jsonData: jsonData && typeof jsonData === "object" ? (jsonData as GrafoJsonData) : null,
    fechaCreacion: asString(pick(obj, "fecha_creacion", "fechaCreacion")),
    scope: scope === "PRIVATE" ? "PRIVATE" : "BASE",
    releaseId: pick(obj, "release_id", "releaseId") ? asString(pick(obj, "release_id", "releaseId")) : undefined,
    generation: pick(obj, "generation") == null ? undefined : asNumber(pick(obj, "generation")),
  }
}

export function mapGrafoList(raw: unknown): GrafoResponse[] {
  return Array.isArray(raw) ? raw.map(mapGrafo) : []
}

export function mapSpringPageGrafos(raw: unknown): SpringPage<GrafoResponse> {
  const obj = asRecord(raw)
  const content = pick(obj, "content")
  return {
    content: Array.isArray(content) ? content.map(mapGrafo) : [],
    totalElements: asNumber(pick(obj, "totalElements")),
    totalPages: asNumber(pick(obj, "totalPages")),
    size: asNumber(pick(obj, "size"), 10),
    number: asNumber(pick(obj, "number")),
  }
}

export function consultaTitulo(item: ConsultaResponse): string {
  if (item.pregunta.trim()) return item.pregunta.trim()
  if (item.respuesta.trim()) {
    const line = item.respuesta.trim().split(/\n/)[0] ?? ""
    return line.length > 80 ? `${line.slice(0, 77)}…` : line
  }
  return item.categoriaFuentePrincipal || "Consulta GraphRAG"
}
