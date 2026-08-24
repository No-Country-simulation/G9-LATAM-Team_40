export type IndiceEstadoNombre =
  | "IDLE"
  | "DIRTY"
  | "QUEUED"
  | "RUNNING"
  | "SUCCEEDED"
  | "FAILED"

export interface IndiceEstado {
  estado: IndiceEstadoNombre
  etapa?: string
  mensaje?: string
  release_id?: string
  generation?: number
  rebuild_pendiente: boolean
  actualizado_en?: string
}
