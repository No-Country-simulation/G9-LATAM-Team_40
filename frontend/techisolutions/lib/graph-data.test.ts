import { describe, expect, it } from "vitest"

import {
  buildGraphExplorerIndex,
  buildGraphRagView,
  filterGraphExplorer,
  getGraphStats,
} from "@/lib/graph-data"
import type { GrafoJsonData } from "@/types/grafo.types"

const json: GrafoJsonData = {
  grafo_conceptual: {
    nivel_1_categorias: [
      {
        id: "cat-seguridad",
        titulo: "Seguridad operacional",
        confianza: 0.92,
        descripcion: "Obligaciones y controles del sistema.",
      },
      {
        id: "cat-archivo",
        titulo: "Archivo histórico",
        confianza: 0.71,
        descripcion: "Material de consulta.",
      },
    ],
    nivel_2_subcategorias: [
      ...Array.from({ length: 81 }, (_, index) => ({
        id: `child-${index}`,
        parent_id: "cat-seguridad",
        titulo_nodo_2:
          index === 0
            ? "Obligación operativa"
            : index === 80
              ? "Nodo fuera del límite"
              : `Procedimiento ${index}`,
        secciones: [
          {
            documento_id: index === 1 ? "doc-compartido" : `doc-${index}`,
            titulo: index === 0 ? "Sección crítica" : `Sección ${index}`,
          },
        ],
      })),
      {
        id: "child-archivo",
        parent_id: "cat-archivo",
        titulo_nodo_2: "Registro documental",
        secciones: [{ documento_id: "doc-archivo", titulo: "Índice" }],
      },
    ],
    nivel_3_relaciones: [
      {
        id: "group-0",
        parent_id: "child-0",
        titulonodo_nivel_3: "Control de riesgo",
        relaciones: [
          {
            documento_id: "doc-relacion",
            titulo_seccion: "Sección crítica",
            sujeto: "Riesgo",
            relacion: "exige",
            objeto: "control",
          },
        ],
      },
      {
        id: "group-80",
        parent_id: "child-80",
        titulonodo_nivel_3: "Seguimiento",
        relaciones: [
          {
            documento_id: "doc-relacion-80",
            titulo_seccion: "Sección 80",
            sujeto: "Auditoría",
            relacion: "verifica",
            objeto: "evidencia",
          },
        ],
      },
    ],
  },
}

describe("graph exploration index", () => {
  it("derives ordered hierarchy, unique documents, and real relations", () => {
    const index = buildGraphExplorerIndex(json)
    const security = index[0]
    const firstChild = security?.children[0]

    expect(getGraphStats(json)).toEqual({
      categories: 2,
      subcategories: 82,
      relations: 2,
      documents: 82,
    })
    expect(security?.children[0]?.id).toBe("child-0")
    expect(security?.children[80]?.id).toBe("child-80")
    expect(security?.documentIds).toContain("doc-0")
    expect(security?.documentIds).toContain("doc-compartido")
    expect(security?.documentCount).toBe(81)
    expect(firstChild?.relations[0]).toMatchObject({
      groupId: "group-0",
      groupTitle: "Control de riesgo",
      documento_id: "doc-relacion",
    })
    expect(firstChild?.relationCount).toBe(1)
  })

  it("matches accents, deep relation fields, and document identifiers", () => {
    const index = buildGraphExplorerIndex(json)

    expect(filterGraphExplorer(index, "OBLIGACIÓN OPERATIVA")[0]?.children).toHaveLength(1)
    expect(filterGraphExplorer(index, "doc-relacion")[0]?.children[0]?.id).toBe(
      "child-0"
    )
    expect(filterGraphExplorer(index, "DOC-80")[0]?.children[0]?.id).toBe(
      "child-80"
    )
    expect(filterGraphExplorer(index, "seguridad")[0]?.children).toHaveLength(81)
    expect(filterGraphExplorer(index, "   ")).toBe(index)
  })

  it("preserves a focused child outside the canvas cap", () => {
    const graph = buildGraphRagView(json, "cat-seguridad", "child-80")
    const childNodes = graph.nodes.filter((node) => node.kind === "n2")

    expect(childNodes).toHaveLength(80)
    expect(childNodes.some((node) => node.id === "child-80")).toBe(true)
    expect(childNodes.some((node) => node.id === "child-79")).toBe(false)
    expect(childNodes.find((node) => node.id === "child-80")).toMatchObject({
      categoryId: "cat-seguridad",
      relationCount: 1,
    })
  })
})
