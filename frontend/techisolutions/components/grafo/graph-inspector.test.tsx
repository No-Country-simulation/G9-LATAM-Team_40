import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { GraphInspector } from "@/components/grafo/graph-inspector"
import type {
  GraphExplorerCategory,
  GraphExplorerChild,
} from "@/lib/graph-data"

const child: GraphExplorerChild = {
  id: "child-1",
  parentId: "cat-1",
  title: "Controles de acceso",
  sections: [
    { documento_id: "doc-1", titulo: "Accesos" },
    { documento_id: "doc-1", titulo: "Accesos" },
    { documento_id: "doc-1", titulo: "Revisión" },
    { documento_id: "doc-2", titulo: "Registro" },
  ],
  relations: [
    {
      groupId: "group-1",
      groupTitle: "Autorización",
      documento_id: "doc-1",
      titulo_seccion: "Accesos",
      sujeto: "Rol",
      relacion: "requiere",
      objeto: "permiso",
    },
    {
      groupId: "group-1",
      groupTitle: "Autorización",
      documento_id: "doc-2",
      titulo_seccion: "Registro",
      sujeto: "Sistema",
      relacion: "registra",
      objeto: "evento",
    },
    {
      groupId: "group-2",
      groupTitle: "Auditoría",
      documento_id: "doc-3",
      titulo_seccion: "Revisión",
      sujeto: "Auditor",
      relacion: "verifica",
      objeto: "control",
    },
  ],
  documentIds: ["doc-1", "doc-2"],
  sectionCount: 4,
  documentCount: 2,
  relationCount: 3,
}

const category: GraphExplorerCategory = {
  id: "cat-1",
  title: "Seguridad",
  description: "Protección del sistema.",
  confidence: 0.88,
  children: [child],
  documentIds: ["doc-1", "doc-2"],
  childCount: 1,
  sectionCount: 4,
  documentCount: 2,
  relationCount: 3,
}

describe("GraphInspector", () => {
  it("asks for a selection when the desk has no category", () => {
    render(<GraphInspector category={null} child={null} />)

    expect(
      screen.getByText(
        "Selecciona una categoría o un tema en el índice o en el plano."
      )
    ).toBeInTheDocument()
    expect(screen.getByText("Esperando selección")).toBeInTheDocument()
  })

  it("explains category meaning without duplicating topic cards", () => {
    render(<GraphInspector category={category} child={null} />)

    expect(screen.getByRole("heading", { name: "Seguridad" })).toBeInTheDocument()
    expect(screen.getByText("Protección del sistema.")).toBeInTheDocument()
    expect(
      screen.getByText("Confianza de clasificación: 88%")
    ).toBeInTheDocument()
    expect(screen.getByText("Temas")).toBeInTheDocument()
    expect(
      screen.getByText(
        "Elige un tema en el índice o en el plano para revisar sus fuentes."
      )
    ).toBeInTheDocument()
    expect(screen.queryByRole("button")).not.toBeInTheDocument()
  })

  it("groups unique sections and shows every semantic connection", () => {
    render(<GraphInspector category={category} child={child} />)

    expect(
      screen.getByText("2 documentos · 4 secciones · 3 conexiones")
    ).toBeInTheDocument()
    expect(screen.getAllByText("Accesos", { exact: true })).toHaveLength(1)
    expect(screen.getByText("doc-1")).toBeInTheDocument()
    expect(screen.getByText("doc-2")).toBeInTheDocument()
    expect(screen.getByText("Rol")).toBeInTheDocument()
    expect(screen.getByText("Sistema")).toBeInTheDocument()
    expect(screen.getByText("Auditor")).toBeInTheDocument()
    expect(
      screen.getByText("Conexiones encontradas (3)")
    ).toBeInTheDocument()
    expect(document.body.textContent).toContain("Fuente: Revisión · doc-3")
    expect(document.body.textContent).toContain("Agrupación: Auditoría")
  })

  it("keeps explicit empty source and connection states", () => {
    const emptyChild: GraphExplorerChild = {
      ...child,
      sections: [],
      relations: [],
      documentIds: [],
      sectionCount: 0,
      documentCount: 0,
      relationCount: 0,
    }
    render(<GraphInspector category={category} child={emptyChild} />)

    expect(
      screen.getByText("No hay documentos asociados a este tema.")
    ).toBeInTheDocument()
    expect(
      screen.getByText("No hay secciones asociadas a este tema.")
    ).toBeInTheDocument()
    expect(
      screen.getByText("No se encontraron conexiones semánticas para este tema.")
    ).toBeInTheDocument()
  })
})
