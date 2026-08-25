import type {
  GrafoJsonData,
  GrafoRelacionN3,
  GrafoRelacionN3Item,
  GrafoSeccionRef,
} from "@/types/grafo.types"

export const N2_CAP = 24

export type GraphNodeKind = "n1" | "n2"

export type GraphNode = {
  id: string
  name: string
  kind: GraphNodeKind
  categoryId: string
  descripcion?: string
  confianza?: number
  parentId?: string
  sectionCount: number
  documentCount: number
  relationCount: number
  color: string
  val: number
}

export type GraphLink = {
  source: string
  target: string
}

export type GraphData = {
  nodes: GraphNode[]
  links: GraphLink[]
}

export type GraphExplorerRelation = GrafoRelacionN3Item & {
  groupId: string
  groupTitle: string
}

export type GraphExplorerChild = {
  id: string
  parentId: string
  title: string
  sections: GrafoSeccionRef[]
  relations: GraphExplorerRelation[]
  documentIds: string[]
  sectionCount: number
  documentCount: number
  relationCount: number
}

export type GraphExplorerCategory = {
  id: string
  title: string
  description: string
  confidence: number
  children: GraphExplorerChild[]
  documentIds: string[]
  childCount: number
  sectionCount: number
  documentCount: number
  relationCount: number
}

export type GraphStats = {
  categories: number
  subcategories: number
  relations: number
  documents: number
}

const PALETTE = [
  "#1a3a5c",
  "#2c5282",
  "#f0c419",
  "#8b7355",
  "#c0392b",
  "#2f6f4e",
  "#6b3fa0",
]

type GraphExplorerContext = {
  index: GraphExplorerCategory[]
  categoryById: Map<string, GraphExplorerCategory>
  childById: Map<string, GraphExplorerChild>
  stats: GraphStats
}

export function hashColor(id: string): string {
  let h = 0
  for (const ch of id) h = (h * 31 + ch.charCodeAt(0)) >>> 0
  return PALETTE[h % PALETTE.length] ?? "#1a3a5c"
}

export function stripMarkdown(text: string): string {
  return text
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
    .replace(/\[([^\]]+)\]\[[^\]]*\]/g, "$1")
    .replace(/^\s{0,3}#{1,6}\s*/gm, "")
    .replace(/(^|\s)#{1,6}\s+/g, "$1")
    .replace(/^\s*(?:[-*+]|\d+\.)\s+/gm, "")
    .replace(/(^|\s)>\s+/g, "$1")
    .replace(/(^|\s)(?:-{3,}|\*{3,}|_{3,})(?=\s|$)/g, "$1")
    .replace(/(\*\*|__|~~|`)/g, "")
    .replace(
      /(^|[\s([{])\*([^*]+?)\*(?=$|[\s)\]}.,!?])/g,
      "$1$2"
    )
    .replace(
      /(^|[\s([{])_([^_]+?)_(?=$|[\s)\]}.,!?])/g,
      "$1$2"
    )
    .replace(/\|/g, " ")
    .replace(/\s+/g, " ")
    .trim()
}

export function shortLabel(text: string, max = 42): string {
  const clean = stripMarkdown(text)
  return clean.length > max ? `${clean.slice(0, max - 1)}…` : clean
}

function uniqueDocumentIds(sections: GrafoSeccionRef[]): string[] {
  const seen = new Set<string>()
  const documentIds: string[] = []
  for (const section of sections) {
    const documentId = section.documento_id.trim()
    if (!documentId || seen.has(documentId)) continue
    seen.add(documentId)
    documentIds.push(documentId)
  }
  return documentIds
}

function categoryFromChildren(
  category: Pick<GraphExplorerCategory, "id" | "title" | "description" | "confidence">,
  children: GraphExplorerChild[]
): GraphExplorerCategory {
  const documentIds = uniqueDocumentIds(
    children.flatMap((child) =>
      child.documentIds.map((documento_id) => ({
        documento_id,
        titulo: "",
      }))
    )
  )
  return {
    ...category,
    children,
    documentIds,
    childCount: children.length,
    sectionCount: children.reduce((total, child) => total + child.sectionCount, 0),
    documentCount: documentIds.length,
    relationCount: children.reduce(
      (total, child) => total + child.relationCount,
      0
    ),
  }
}

function createGraphExplorerContext(
  json: GrafoJsonData | null
): GraphExplorerContext {
  const conceptual = json?.grafo_conceptual
  if (!conceptual) {
    return {
      index: [],
      categoryById: new Map(),
      childById: new Map(),
      stats: { categories: 0, subcategories: 0, relations: 0, documents: 0 },
    }
  }

  const categories = conceptual.nivel_1_categorias ?? []
  const subcategories = conceptual.nivel_2_subcategorias ?? []
  const relationGroups = conceptual.nivel_3_relaciones ?? []
  const groupsByParent = new Map<string, GrafoRelacionN3[]>()

  for (const group of relationGroups) {
    const groups = groupsByParent.get(group.parent_id) ?? []
    groups.push(group)
    groupsByParent.set(group.parent_id, groups)
  }

  const childrenByCategory = new Map<string, GraphExplorerChild[]>()
  const childById = new Map<string, GraphExplorerChild>()

  for (const subcategory of subcategories) {
    const sections = (subcategory.secciones ?? []).map((section) => ({
      ...section,
      titulo: stripMarkdown(section.titulo),
    }))
    const groups = groupsByParent.get(subcategory.id) ?? []
    const relations = groups.flatMap((group) =>
      (group.relaciones ?? []).map((relation) => ({
        ...relation,
        titulo_seccion: stripMarkdown(relation.titulo_seccion),
        sujeto: stripMarkdown(relation.sujeto),
        relacion: stripMarkdown(relation.relacion),
        objeto: stripMarkdown(relation.objeto),
        groupId: group.id,
        groupTitle: stripMarkdown(group.titulonodo_nivel_3),
      }))
    )
    const documentIds = uniqueDocumentIds(sections)
    const child: GraphExplorerChild = {
      id: subcategory.id,
      parentId: subcategory.parent_id,
      title: stripMarkdown(subcategory.titulo_nodo_2),
      sections,
      relations,
      documentIds,
      sectionCount: sections.length,
      documentCount: documentIds.length,
      relationCount: relations.length,
    }
    childById.set(child.id, child)
    const children = childrenByCategory.get(child.parentId) ?? []
    children.push(child)
    childrenByCategory.set(child.parentId, children)
  }

  const index = categories.map((category) =>
    categoryFromChildren(
      {
        id: category.id,
        title: stripMarkdown(category.titulo),
        description: stripMarkdown(category.descripcion ?? ""),
        confidence: category.confianza,
      },
      childrenByCategory.get(category.id) ?? []
    )
  )
  const categoryById = new Map(index.map((category) => [category.id, category]))
  const documentIds = uniqueDocumentIds(
    subcategories.flatMap((subcategory) => subcategory.secciones ?? [])
  )

  return {
    index,
    categoryById,
    childById,
    stats: {
      categories: categories.length,
      subcategories: subcategories.length,
      relations: relationGroups.reduce(
        (total, group) => total + (group.relaciones?.length ?? 0),
        0
      ),
      documents: documentIds.length,
    },
  }
}

export function buildGraphExplorerIndex(
  json: GrafoJsonData | null
): GraphExplorerCategory[] {
  return createGraphExplorerContext(json).index
}

export function getGraphStats(json: GrafoJsonData | null): GraphStats {
  return createGraphExplorerContext(json).stats
}

function normalizeSearch(value: string): string {
  return value
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLocaleUpperCase("es-CL")
    .replace(/\s+/g, " ")
    .trim()
}

function includesQuery(value: string | undefined, query: string): boolean {
  return Boolean(value && normalizeSearch(value).includes(query))
}

function childMatches(child: GraphExplorerChild, query: string): boolean {
  if (includesQuery(child.id, query) || includesQuery(child.title, query)) {
    return true
  }
  if (
    child.sections.some(
      (section) =>
        includesQuery(section.documento_id, query) ||
        includesQuery(section.titulo, query)
    )
  ) {
    return true
  }
  return child.relations.some((relation) =>
    [
      relation.sujeto,
      relation.relacion,
      relation.objeto,
      relation.documento_id,
    ].some((value) => includesQuery(value, query))
  )
}

export function filterGraphExplorer(
  index: GraphExplorerCategory[],
  query: string
): GraphExplorerCategory[] {
  const normalizedQuery = normalizeSearch(query)
  if (!normalizedQuery) return index

  return index.flatMap((category) => {
    if (
      includesQuery(category.title, normalizedQuery) ||
      includesQuery(category.description, normalizedQuery)
    ) {
      return [category]
    }
    const children = category.children.filter((child) =>
      childMatches(child, normalizedQuery)
    )
    return children.length > 0
      ? [categoryFromChildren(category, children)]
      : []
  })
}

export function buildGraphRagView(
  json: GrafoJsonData | null,
  selectedCategoryId: string | null,
  focusedNodeId: string | null = null
): GraphData {
  const context = createGraphExplorerContext(json)
  const visibleCategories = selectedCategoryId
    ? context.index.filter((category) => category.id === selectedCategoryId)
    : context.index
  const nodes: GraphNode[] = visibleCategories.map((category) => ({
    id: category.id,
    name: category.title,
    kind: "n1",
    categoryId: category.id,
    descripcion: category.description,
    confianza: category.confidence,
    sectionCount: category.sectionCount,
    documentCount: category.documentCount,
    relationCount: category.relationCount,
    color: hashColor(category.id),
    val: 1.4 + category.confidence,
  }))
  const links: GraphLink[] = []

  if (selectedCategoryId) {
    const category = context.categoryById.get(selectedCategoryId)
    const children = category?.children ?? []
    const visibleChildren = children.slice(0, N2_CAP)
    const focusedChild =
      focusedNodeId && context.childById.get(focusedNodeId)?.parentId === selectedCategoryId
        ? context.childById.get(focusedNodeId)
        : undefined

    if (focusedChild && !visibleChildren.some((child) => child.id === focusedChild.id)) {
      if (visibleChildren.length >= N2_CAP) {
        visibleChildren[visibleChildren.length - 1] = focusedChild
      } else {
        visibleChildren.push(focusedChild)
      }
    }

    for (const child of visibleChildren) {
      nodes.push({
        id: child.id,
        name: shortLabel(child.title),
        kind: "n2",
        categoryId: child.parentId,
        parentId: child.parentId,
        descripcion: child.title,
        sectionCount: child.sectionCount,
        documentCount: child.documentCount,
        relationCount: child.relationCount,
        color: hashColor(child.parentId),
        val: 0.8 + Math.min(child.relationCount / 20, 0.8),
      })
      links.push({ source: selectedCategoryId, target: child.id })
    }
  }

  return { nodes, links }
}
