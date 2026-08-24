import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

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
  sectionCount: 3,
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
  sectionCount: 3,
  documentCount: 2,
  relationCount: 3,
}

const stats = { categories: 1, subcategories: 1, relations: 3, documents: 2 }

describe("GraphInspector", () => {
  it("shows category detail and child access", () => {
    const onSelectChild = vi.fn()
    render(
      <GraphInspector
        stats={stats}
        category={category}
        child={null}
        onSelectChild={onSelectChild}
      />
    )

    expect(screen.getByText("Protección del sistema.")).toBeInTheDocument()
    expect(screen.getByText("88% confianza")).toBeInTheDocument()
    expect(screen.getByText("Documentos únicos")).toBeInTheDocument()
    fireEvent.click(screen.getByRole("button", { name: /Controles de acceso/ }))
    expect(onSelectChild).toHaveBeenCalledWith("child-1")
  })

  it("shows unique documents and every N3 relation", () => {
    render(
      <GraphInspector
        stats={stats}
        category={category}
        child={child}
        onSelectChild={vi.fn()}
      />
    )

    expect(screen.getByText("2 documentos únicos · 3 secciones · 3 relaciones")).toBeInTheDocument()
    expect(screen.getAllByText("doc-1").length).toBeGreaterThan(0)
    expect(screen.getByText("doc-2")).toBeInTheDocument()
    expect(screen.getByText("Rol")).toBeInTheDocument()
    expect(screen.getByText("Sistema")).toBeInTheDocument()
    expect(screen.getByText("Auditor")).toBeInTheDocument()
    expect(screen.getByText("Relaciones N3 (3)")).toBeInTheDocument()
    expect(document.body.textContent).toContain("Sección: Revisión")
  })
})
