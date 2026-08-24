export interface GrafoSeccionRef {
  documento_id: string
  titulo: string
}

export interface GrafoCategoriaN1 {
  id: string
  titulo: string
  confianza: number
  descripcion: string
}

export interface GrafoSubcategoriaN2 {
  id: string
  parent_id: string
  titulo_nodo_2: string
  secciones?: GrafoSeccionRef[]
}

export interface GrafoRelacionN3Item {
  documento_id: string
  titulo_seccion: string
  sujeto: string
  relacion: string
  objeto: string
  tipo_relacion?: string
  contexto?: string
  origen?: string
  confianza?: number
}

export interface GrafoRelacionN3 {
  id: string
  parent_id: string
  titulonodo_nivel_3: string
  relaciones: GrafoRelacionN3Item[]
}

export interface GrafoConceptual {
  nivel_1_categorias: GrafoCategoriaN1[]
  nivel_2_subcategorias: GrafoSubcategoriaN2[]
  nivel_3_relaciones: GrafoRelacionN3[]
}

export interface GrafoJsonData {
  grafo_conceptual?: GrafoConceptual
}

export interface GrafoResponse {
  id: string
  jsonData: GrafoJsonData | null
  fechaCreacion: string
  scope: "BASE" | "PRIVATE"
  releaseId?: string
  generation?: number
}

export interface SpringPage<T> {
  content: T[]
  totalElements: number
  totalPages: number
  size: number
  number: number
}
