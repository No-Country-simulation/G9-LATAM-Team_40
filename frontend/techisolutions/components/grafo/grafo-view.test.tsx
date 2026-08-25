import type { ReactNode } from "react"

import { act, fireEvent, render, screen, waitFor } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import type { GrafoJsonData, GrafoResponse } from "@/types/grafo.types"

const {
  getBase,
  getPrivate,
  getById,
  getHistory,
  getIndex,
} = vi.hoisted(() => ({
  getBase: vi.fn(),
  getPrivate: vi.fn(),
  getById: vi.fn(),
  getHistory: vi.fn(),
  getIndex: vi.fn(),
}))

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}))

vi.mock("@/components/auth/auth-gate", () => ({
  AuthGate: ({ children }: { children: ReactNode }) => children,
}))

vi.mock("@/components/clipboard/app-shell", () => ({
  AppShell: ({ children }: { children: ReactNode }) => <main>{children}</main>,
}))

vi.mock("@/components/grafo/graph-observatory-canvas", () => ({
  GraphObservatoryCanvas: () => <div data-testid="graph-canvas" />,
}))

vi.mock("@/services/grafo.service", () => ({
  obtenerGrafoActual: getBase,
  obtenerGrafoPrivado: getPrivate,
  obtenerGrafoPorId: getById,
  listarHistorialGrafos: getHistory,
  buscarGrafosPorFecha: vi.fn(),
}))

vi.mock("@/services/indice.service", () => ({ obtenerIndice: getIndex }))

import { GrafoView } from "@/components/grafo/grafo-view"

const graphJson: GrafoJsonData = {
  grafo_conceptual: {
    nivel_1_categorias: [
      {
        id: "cat-1",
        titulo: "**Seguridad**",
        confianza: 0.9,
        descripcion: "## Controles institucionales.",
      },
    ],
    nivel_2_subcategorias: [
      {
        id: "child-1",
        parent_id: "cat-1",
        titulo_nodo_2: "**Controles**",
        secciones: [{ documento_id: "doc-1", titulo: "**Sección**" }],
      },
    ],
    nivel_3_relaciones: [
      {
        id: "group-1",
        parent_id: "child-1",
        titulonodo_nivel_3: "**Controles de riesgo**",
        relaciones: [
          {
            documento_id: "doc-1",
            titulo_seccion: "**Sección**",
            sujeto: "**Riesgo**",
            relacion: "requiere",
            objeto: "_control_",
          },
        ],
      },
    ],
  },
}

const privateGraphJson: GrafoJsonData = {
  grafo_conceptual: {
    ...graphJson.grafo_conceptual!,
    nivel_1_categorias: [
      {
        id: "cat-1",
        titulo: "**Seguridad**",
        confianza: 0.9,
      },
    ],
  },
}

const baseSnapshot: GrafoResponse = {
  id: "base-1",
  jsonData: graphJson,
  fechaCreacion: "2026-08-24T10:00:00Z",
  scope: "BASE",
}

const selectedSnapshot: GrafoResponse = {
  ...baseSnapshot,
  id: "base-2",
  fechaCreacion: "2026-08-25T10:00:00Z",
}

const privateSnapshot: GrafoResponse = {
  id: "private-1",
  jsonData: privateGraphJson,
  fechaCreacion: "2026-08-26T10:00:00Z",
  scope: "PRIVATE",
  releaseId: "release-private-123",
  generation: 3,
}

const page = {
  content: [baseSnapshot],
  totalElements: 1,
  totalPages: 1,
  size: 8,
  number: 0,
}

function installDialogMocks() {
  Object.defineProperty(HTMLDialogElement.prototype, "showModal", {
    configurable: true,
    value() {
      this.setAttribute("open", "")
    },
  })
  Object.defineProperty(HTMLDialogElement.prototype, "close", {
    configurable: true,
    value() {
      this.removeAttribute("open")
    },
  })
}
afterEach(() => {
  vi.useRealTimers()
})

describe("GrafoView", () => {
  beforeEach(() => {
    getBase.mockResolvedValue(baseSnapshot)
    getPrivate.mockResolvedValue(privateSnapshot)
    getById.mockResolvedValue(selectedSnapshot)
    getHistory.mockResolvedValue(page)
    getIndex.mockResolvedValue({ estado: "SUCCEEDED", release_id: "release-private-123" })
    installDialogMocks()
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: () => ({
        matches: false,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }),
    })
  })

  it("guides category, topic, and source evidence", async () => {
    render(<GrafoView />)

    await waitFor(() =>
      expect(
        screen.getByText(
          "Selecciona una categoría o un tema en el índice o en el plano."
        )
      ).toBeInTheDocument()
    )
    expect(screen.getByRole("button", { name: "Biblioteca general" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Ver versiones" })).toBeInTheDocument()
    expect(screen.getByText(/Actualizado/)).toBeInTheDocument()
    expect(screen.getByText("Todas las categorías")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /Seguridad/ })).toBeInTheDocument()

    fireEvent.click(screen.getByRole("button", { name: /Seguridad/ }))
    expect(screen.getByText("Temas de Seguridad")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /Controles/ })).toBeInTheDocument()
    fireEvent.click(screen.getByRole("button", { name: /Controles/ }))

    expect(screen.getByText("Conexiones encontradas (1)")).toBeInTheDocument()
    expect(document.body.textContent).toContain("Fuente: Sección · doc-1")
    expect(document.body.textContent).toContain("Agrupación: Controles de riesgo")
    expect(document.body.textContent).not.toContain("N1")
    expect(document.body.textContent).not.toContain("N2")
    expect(document.body.textContent).not.toContain("N3")
    expect(document.body.textContent).not.toMatch(/snapshot|release/i)
  })
  it("clears topic detail on search and resets the desk", async () => {
    render(<GrafoView />)
    await waitFor(() =>
      expect(
        screen.getByText(
          "Selecciona una categoría o un tema en el índice o en el plano."
        )
      ).toBeInTheDocument()
    )

    fireEvent.click(screen.getByRole("button", { name: /Seguridad/ }))
    fireEvent.click(screen.getByRole("button", { name: /Controles/ }))
    const search = screen.getByPlaceholderText("Categoría, tema o documento")
    fireEvent.change(search, { target: { value: "doc-1" } })

    expect(screen.getByText("Temas de Seguridad")).toBeInTheDocument()
    expect(
      screen.getByText(
        "Elige un tema en el índice o en el plano para revisar sus fuentes."
      )
    ).toBeInTheDocument()

    fireEvent.click(screen.getByRole("button", { name: "Ver todo el mapa" }))
    expect(
      screen.getByText(
        "Selecciona una categoría o un tema en el índice o en el plano."
      )
    ).toBeInTheDocument()
    expect(
      screen.getByPlaceholderText("Categoría, tema o documento")
    ).toHaveValue("")
  })


  it("loads private documents with friendly status and no BASE history", async () => {
    render(<GrafoView />)
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Mis documentos" })).toBeInTheDocument()
    )

    fireEvent.click(screen.getByRole("button", { name: "Mis documentos" }))
    await waitFor(() => expect(getPrivate).toHaveBeenCalled())

    expect(screen.queryByRole("button", { name: "Ver versiones" })).not.toBeInTheDocument()
    expect(screen.getByText("Tus documentos están actualizados")).toBeInTheDocument()
    expect(document.body.textContent).not.toMatch(/release|generación/i)
    expect(screen.getByRole("button", { name: /Seguridad/ })).toBeInTheDocument()
  })
  it("reloads the private graph after indexing transitions to succeeded", async () => {
    vi.useFakeTimers()
    getPrivate.mockClear()
    getIndex.mockReset()
    getIndex
      .mockResolvedValueOnce({ estado: "RUNNING" })
      .mockResolvedValueOnce({ estado: "SUCCEEDED" })

    render(<GrafoView />)
    await act(async () => {
      vi.runOnlyPendingTimers()
      await Promise.resolve()
      await Promise.resolve()
    })

    fireEvent.click(screen.getByRole("button", { name: "Mis documentos" }))
    await act(async () => {
      vi.runOnlyPendingTimers()
      await Promise.resolve()
      await Promise.resolve()
    })
    expect(getPrivate).toHaveBeenCalledTimes(1)

    await act(async () => {
      vi.advanceTimersByTime(5000)
      await Promise.resolve()
      await Promise.resolve()
      await Promise.resolve()
    })

    expect(getPrivate).toHaveBeenCalledTimes(2)
  })

  it("offers /archivos when PRIVATE has no published graph", async () => {
    getPrivate.mockResolvedValue({
      ...privateSnapshot,
      jsonData: null,
      releaseId: undefined,
      generation: undefined,
    })
    render(<GrafoView />)
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Mis documentos" })).toBeInTheDocument()
    )

    fireEvent.click(screen.getByRole("button", { name: "Mis documentos" }))
    await waitFor(() =>
      expect(
        screen.getByText("Tu biblioteca todavía no tiene un mapa publicado.")
      ).toBeInTheDocument()
    )
    expect(screen.getByRole("link", { name: "Subir documentos" })).toHaveAttribute(
      "href",
      "/archivos"
    )
  })

  it("loads a historical version and closes the version drawer", async () => {
    render(<GrafoView />)
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Ver versiones" })).toBeInTheDocument()
    )

    fireEvent.click(screen.getByRole("button", { name: "Ver versiones" }))
    const dialog = screen.getByRole("dialog", {
      name: "Versiones de la biblioteca general",
    })
    expect(dialog).toHaveAttribute("open")
    fireEvent.click(screen.getByRole("button", { name: /24/ }))

    await waitFor(() => expect(getById).toHaveBeenCalledWith("base-1"))
    await waitFor(() => expect(screen.getByText(/Actualizado.*25/)).toBeInTheDocument())
    expect(dialog).not.toHaveAttribute("open")
  })
})
