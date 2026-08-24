import { consultaTitulo } from "@/lib/api-mappers"
import { listarArchivos } from "@/services/archivo.service"
import { buscarConsultas } from "@/services/consulta.service"

export type SearchHit =
  | {
      kind: "consulta"
      id: string
      titulo: string
      categoria: string
      relevancia: number
      palabrasClave: string[]
      href: string
    }
  | {
      kind: "archivo"
      id: string
      nombre: string
      tipo: string
      tamano: number
      href: string
    }

function normalize(value: string): string {
  return value.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase().trim()
}

function includesQuery(haystack: string, query: string): boolean {
  return normalize(haystack).includes(query)
}

export function matchesConsultaQuery(
  consulta: {
    pregunta: string
    categoriaFuentePrincipal: string
    palabrasClave: readonly string[]
    respuesta?: string
  },
  rawQuery: string
): boolean {
  const query = normalize(rawQuery)
  if (!query) return true
  if (includesQuery(consulta.pregunta, query)) return true
  if (includesQuery(consulta.categoriaFuentePrincipal, query)) return true
  if (consulta.respuesta && includesQuery(consulta.respuesta, query)) return true
  return consulta.palabrasClave.some((keyword) => includesQuery(keyword, query))
}

export async function searchRemote(rawQuery: string): Promise<SearchHit[]> {
  const query = rawQuery.trim()
  if (!query) return []
  const [consultas, archivosPage] = await Promise.all([
    buscarConsultas(query),
    listarArchivos({ page: 0, size: 10, q: query }),
  ])
  const hits: SearchHit[] = consultas.slice(0, 12).map((item) => ({
    kind: "consulta",
    id: item.id,
    titulo: consultaTitulo(item),
    categoria: item.categoriaFuentePrincipal,
    relevancia: item.relevancia,
    palabrasClave: item.palabrasClave,
    href: `/consultar?consulta=${encodeURIComponent(item.id)}`,
  }))
  hits.push(...archivosPage.items.map((file) => ({
    kind: "archivo" as const,
    id: file.id,
    nombre: file.nombre,
    tipo: file.tipo,
    tamano: file.tamano,
    href: `/archivos?file=${encodeURIComponent(file.id)}`,
  })))
  return hits.slice(0, 20)
}
