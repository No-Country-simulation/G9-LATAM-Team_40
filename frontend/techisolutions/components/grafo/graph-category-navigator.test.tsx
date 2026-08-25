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
      selectedCategoryId={null}
      selectedNodeId={null}
      onQueryChange={vi.fn()}
      onReset={vi.fn()}
      onSelectCategory={vi.fn()}
      onSelectChild={vi.fn()}
      {...overrides}
    />
  )
}

describe("GraphCategoryNavigator", () => {
  it("lists categories and emits document searches", () => {
    const onQueryChange = vi.fn()
    renderNavigator({ onQueryChange })

    expect(screen.getByText("Categorías y temas")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /Seguridad operacional/ })).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: /Controles críticos/ })).not.toBeInTheDocument()
    fireEvent.change(
      screen.getByPlaceholderText("Categoría, tema o documento"),
      { target: { value: "doc-1" } }
    )
    expect(onQueryChange).toHaveBeenCalledWith("doc-1")
  })

  it("expands topics in place with full count labels", () => {
    const onSelectChild = vi.fn()
    renderNavigator({
      selectedCategoryId: "cat-security",
      onSelectChild,
    })

    expect(screen.getByRole("button", { name: /Seguridad operacional/ })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Ver todo el mapa" })).toBeInTheDocument()
    expect(
      screen.getByPlaceholderText("Categoría, tema o documento")
    ).toBeInTheDocument()
    expect(
      screen.getByText("1 sección · 1 documento · 0 conexiones")
    ).toBeInTheDocument()
    fireEvent.click(screen.getByRole("button", { name: /Controles críticos/ }))
    expect(onSelectChild).toHaveBeenCalledWith("child-controls")
  })

  it("reports initial and selected-category no-match states", () => {
    const { rerender } = renderNavigator({
      filteredIndex: [],
      query: "inexistente",
    })
    expect(
      screen.getByText(
        "No encontramos categorías o temas con “inexistente”. Prueba con otro término o identificador de documento."
      )
    ).toBeInTheDocument()

    rerender(
      <GraphCategoryNavigator
        index={[category]}
        filteredIndex={[]}
        query="inexistente"
        selectedCategoryId="cat-security"
        selectedNodeId={null}
        onQueryChange={vi.fn()}
        onReset={vi.fn()}
        onSelectCategory={vi.fn()}
        onSelectChild={vi.fn()}
      />
    )
    expect(
      screen.getByText(
        "No encontramos temas dentro de Seguridad operacional con “inexistente”."
      )
    ).toBeInTheDocument()
  })

  it("calls category and reset callbacks", () => {
    const onSelectCategory = vi.fn()
    renderNavigator({ onSelectCategory })

    fireEvent.click(screen.getByRole("button", { name: /Seguridad operacional/ }))
    expect(onSelectCategory).toHaveBeenCalledWith("cat-security")

    const onReset = vi.fn()
    renderNavigator({ selectedCategoryId: "cat-security", onReset })
    fireEvent.click(screen.getByRole("button", { name: "Ver todo el mapa" }))
    expect(onReset).toHaveBeenCalled()
  })
})
