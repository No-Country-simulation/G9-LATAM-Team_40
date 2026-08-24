export type Corpus = "BASE" | "PRIVADO"

export interface ConsultaRequest {
  pregunta: string
}

export interface TrazabilidadSeccion {
  documentoId: string
  documentoTitulo: string
  categoria: string
  palabrasClave: string[]
  tituloSeccion: string
  rutaJerarquica: string[]
  nivel: number
  dominio: string
  relevancia: number
  corpus: Corpus
  archivoId?: string
}

export interface ConsultaResponse {
  id: string
  pregunta: string
  respuesta: string
  categoriaFuentePrincipal: string
  relevancia: number
  palabrasClave: string[]
  trazabilidad: TrazabilidadSeccion[]
  tiempoSegundos?: number
  procesadoEn: string
}
