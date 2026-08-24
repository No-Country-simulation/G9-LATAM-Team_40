import type { ReactNode } from "react"

import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"

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
        titulo: "Seguridad",
        confianza: 0.9,
        descripcion: "Controles institucionales.",
      },
    ],
    nivel_2_subcategorias: [
      {
        id: "child-1",
        parent_id: "cat-1",
        titulo_nodo_2: "Controles",
        secciones: [{ documento_id: "doc-1", titulo: "Sección" }],
      },
    ],
    nivel_3_relaciones: [],
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
  jsonData: graphJson,
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

  it("shows Snapshots in BASE", async () => {
    render(<GrafoView />)

    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Snapshots" })).toBeInTheDocument()
    )
    expect(getBase).toHaveBeenCalled()
    expect(screen.getByText(/Snapshot base-1/)).toBeInTheDocument()
    expect(screen.getAllByText("Categorías N1").length).toBeGreaterThan(0)
  })

  it("loads Mi corpus, hides BASE history, and shows release status", async () => {
    render(<GrafoView />)
    await waitFor(() => screen.getByRole("button", { name: "Mi corpus" }))

    fireEvent.click(screen.getByRole("button", { name: "Mi corpus" }))
    await waitFor(() => expect(getPrivate).toHaveBeenCalled())

    expect(screen.queryByRole("button", { name: "Snapshots" })).not.toBeInTheDocument()
    expect(screen.getByText(/Release release-/)).toBeInTheDocument()
    expect(screen.getByText("Generación 3")).toBeInTheDocument()
    expect(screen.getByText("Índice · SUCCEEDED")).toBeInTheDocument()
  })

  it("offers /archivos when PRIVATE has no published graph", async () => {
    getPrivate.mockResolvedValue({
      ...privateSnapshot,
      jsonData: null,
      releaseId: undefined,
      generation: undefined,
    })
    render(<GrafoView />)
    await waitFor(() => screen.getByRole("button", { name: "Mi corpus" }))

    fireEvent.click(screen.getByRole("button", { name: "Mi corpus" }))
    await waitFor(() =>
      expect(screen.getByText("Tu corpus aún no tiene un grafo publicado.")).toBeInTheDocument()
    )
    expect(screen.getByRole("link", { name: "Subir documentos" })).toHaveAttribute(
      "href",
      "/archivos"
    )
  })

  it("updates snapshot metadata and closes the drawer after selection", async () => {
    render(<GrafoView />)
    await waitFor(() => screen.getByRole("button", { name: "Snapshots" }))

    fireEvent.click(screen.getByRole("button", { name: "Snapshots" }))
    const dialog = screen.getByRole("dialog", { name: "Snapshots base" })
    expect(dialog).toHaveAttribute("open")
    fireEvent.click(screen.getByRole("button", { name: /base-1/ }))

    await waitFor(() => expect(getById).toHaveBeenCalledWith("base-1"))
    await waitFor(() => expect(screen.getByText(/Snapshot base-2/)).toBeInTheDocument())
    expect(dialog).not.toHaveAttribute("open")
  })
})
