export type ArchivoDominio = "ISOS" | "LEYES"

export interface ArchivoResponse {
  id: string
  nombre: string
  documentoId: string
  dominio?: ArchivoDominio
  tamano: number
  tipo: string
  subidoEn: string
  indexadoEn?: string
  pendienteEliminacion: boolean
}

export interface PaginaResponse<T> {
  items: T[]
  page: number
  size: number
  totalElements: number
  totalPages: number
}

export const ALLOWED_FILE_TYPES = [
  "application/pdf",
  "text/plain",
  "text/markdown",
] as const

export const ALLOWED_FILE_LABELS = "PDF, TXT, MD"
export const MAX_FILE_BYTES = 10 * 1024 * 1024
export type ArchivoTipoFiltro = "pdf" | "txt" | "md" | ""
