import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { GraphCategoryNavigator } from "@/components/grafo/graph-category-navigator"
import type { GraphExplorerCategory } from "@/lib/graph-data"

const child = {
  id: "child-controls",
  parentId: "cat-security",
  title: "Controles críticos",
  sections: [{ documento_id: "doc-1", titulo: "Sección de riesgos" }],
  relations: [],
  documentIds: ["doc-1"],
  sectionCount: 1,
  documentCount: 1,
  relationCount: 0,
}

const category: GraphExplorerCategory = {
  id: "cat-security",
  title: "Seguridad operacional",
  description: "Controles del sistema.",
  confidence: 0.92,
  children: [child],
  documentIds: ["doc-1"],
  childCount: 1,
  sectionCount: 1,
  documentCount: 1,
  relationCount: 0,
}

function renderNavigator(
  overrides: Partial<React.ComponentProps<typeof GraphCategoryNavigator>> = {}
) {
  return render(
    <GraphCategoryNavigator
      index={[category]}
      filteredIndex={[category]}
      query=""
      selectedCategoryId="cat-security"
      selectedNodeId={null}
      onQueryChange={vi.fn()}
      onSelectCategory={vi.fn()}
      onSelectChild={vi.fn()}
      {...overrides}
    />
  )
}

describe("GraphCategoryNavigator", () => {
  it("emits searches and exposes deep matched children", () => {
    const onQueryChange = vi.fn()
    renderNavigator({
      filteredIndex: [{ ...category, children: [child] }],
      onQueryChange,
    })

    fireEvent.change(screen.getByPlaceholderText("Buscar categoría, sección o documento"), {
      target: { value: "doc-1" },
    })
    expect(onQueryChange).toHaveBeenCalledWith("doc-1")
    expect(screen.getByRole("button", { name: /Controles críticos/ })).toBeInTheDocument()
  })

  it("reports an empty filtered state", () => {
    renderNavigator({ filteredIndex: [], query: "inexistente" })
    expect(
      screen.getByText("No hay conceptos que coincidan con esta búsqueda.")
    ).toBeInTheDocument()
  })

  it("calls category and child callbacks with semantic buttons", () => {
    const onSelectCategory = vi.fn()
    const onSelectChild = vi.fn()
    renderNavigator({ onSelectCategory, onSelectChild })

    fireEvent.click(screen.getByRole("button", { name: /Seguridad operacional/ }))
    fireEvent.click(screen.getByRole("button", { name: /Controles críticos/ }))

    expect(onSelectCategory).toHaveBeenCalledWith("cat-security")
    expect(onSelectChild).toHaveBeenCalledWith("child-controls")
  })
})
