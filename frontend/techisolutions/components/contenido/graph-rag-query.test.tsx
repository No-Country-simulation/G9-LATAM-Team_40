import type { ReactNode } from "react"

import { act, fireEvent, render, screen, waitFor } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"

import type { ConsultaResponse } from "@/types/consulta.types"

const { analizarConsulta, obtenerConsulta, replace } = vi.hoisted(() => ({
  analizarConsulta: vi.fn(),
  obtenerConsulta: vi.fn(),
  replace: vi.fn(),
}))

vi.mock("@/services/consulta.service", () => ({ analizarConsulta, obtenerConsulta }))
vi.mock("next/navigation", () => ({ useRouter: () => ({ replace }) }))
vi.mock("@/components/auth/auth-gate", () => ({
  AuthGate: ({ children }: { children: ReactNode }) => <>{children}</>,
}))
vi.mock("@/components/clipboard/app-shell", () => ({
  AppShell: ({ children }: { children: ReactNode }) => <>{children}</>,
}))
vi.mock("@/components/clipboard/form-elements", () => ({
  FormPaper: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}))
vi.mock("@/components/clipboard/form-field", () => ({
  FormAlert: ({ children }: { children: ReactNode }) => <div role="alert">{children}</div>,
}))
vi.mock("@/components/clipboard/graph-rag-result", () => ({
  GraphRagResult: ({ result }: { result: ConsultaResponse }) => (
    <div data-testid="graph-result">
      <p>{result.pregunta}</p>
      <p>{result.respuesta}</p>
      {result.trazabilidad.map((source) => <p key={source.documentoId}>{source.documentoTitulo}</p>)}
    </div>
  ),
}))

import { GraphRagQuery } from "@/components/contenido/graph-rag-query"

const savedResult: ConsultaResponse = {
  id: "query-1",
  pregunta: "¿Qué obligaciones contiene el corpus normativo?",
  respuesta: "Respuesta persistida",
  categoriaFuentePrincipal: "Seguridad",
  relevancia: 0.9,
  palabrasClave: ["riesgo"],
  tiempoSegundos: 1.25,
  procesadoEn: "2026-08-24T10:00:00Z",
  trazabilidad: [{
    documentoId: "doc-1",
    documentoTitulo: "Manual base",
    categoria: "Seguridad",
    palabrasClave: ["riesgo"],
    tituloSeccion: "Obligaciones",
    rutaJerarquica: ["Capítulo 1"],
    nivel: 1,
    dominio: "ISOs",
    relevancia: 0.9,
    corpus: "BASE",
  }],
}

const newResult: ConsultaResponse = {
  ...savedResult,
  id: "query-2",
  pregunta: "¿Qué controles nuevos contiene el corpus normativo?",
  respuesta: "Respuesta nueva",
}
function deferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise
    reject = rejectPromise
  })
  return { promise, resolve, reject }
}

describe("GraphRagQuery", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    obtenerConsulta.mockResolvedValue(savedResult)
    analizarConsulta.mockResolvedValue(newResult)
  })

  it("loads a saved query as one exchange with an empty composer", async () => {
    const saved = deferred<ConsultaResponse>()
    obtenerConsulta.mockReturnValueOnce(saved.promise)

    render(<GraphRagQuery initialConsultaId="query-1" />)

    expect(screen.getByText("Cargando consulta guardada…")).toBeInTheDocument()
    expect(screen.getByRole("textbox")).toBeDisabled()
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled()

    await act(async () => saved.resolve(savedResult))

    await waitFor(() => expect(screen.getByTestId("graph-result")).toBeInTheDocument())
    expect(screen.getByRole("textbox")).toHaveValue("")
    expect(screen.getAllByTestId("graph-result")).toHaveLength(1)
    expect(screen.getByText("Respuesta persistida")).toBeInTheDocument()
    expect(screen.getByText("Manual base")).toBeInTheDocument()
    expect(obtenerConsulta).toHaveBeenCalledTimes(1)
    expect(obtenerConsulta).toHaveBeenCalledWith("query-1")
  })

  it("keeps Nueva conversación available after a saved query error", async () => {
    obtenerConsulta.mockRejectedValueOnce(new Error(""))

    render(<GraphRagQuery initialConsultaId="query-1" />)

    await waitFor(() => expect(screen.getByText("No se pudo abrir la consulta guardada.")).toBeInTheDocument())
    expect(screen.getByRole("button", { name: "Nueva conversación" })).toBeInTheDocument()
    expect(screen.getByRole("textbox")).not.toBeDisabled()
    expect(screen.queryByTestId("graph-result")).not.toBeInTheDocument()
  })

  it("appends a submitted exchange without duplicating the historical GET", async () => {
    const post = deferred<ConsultaResponse>()
    analizarConsulta.mockReturnValueOnce(post.promise)

    const { rerender } = render(<GraphRagQuery initialConsultaId="query-1" />)
    await waitFor(() => expect(screen.getByTestId("graph-result")).toBeInTheDocument())

    fireEvent.change(screen.getByRole("textbox"), { target: { value: newResult.pregunta } })
    fireEvent.click(screen.getByRole("button", { name: "Enviar" }))

    expect(screen.getByText(newResult.pregunta)).toBeInTheDocument()
    expect(screen.getByText("Analizando el corpus…")).toBeInTheDocument()
    expect(screen.getByRole("textbox")).toHaveValue("")
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled()

    await act(async () => post.resolve(newResult))

    await waitFor(() => expect(screen.getAllByTestId("graph-result")).toHaveLength(2))
    expect(screen.getByText("Respuesta persistida")).toBeInTheDocument()
    expect(screen.getByText("Respuesta nueva")).toBeInTheDocument()
    expect(screen.getByRole("textbox")).toHaveValue("")
    expect(replace).toHaveBeenCalledWith("/consultar?consulta=query-2", { scroll: false })

    rerender(<GraphRagQuery initialConsultaId="query-2" />)
    expect(screen.getAllByTestId("graph-result")).toHaveLength(2)
    expect(obtenerConsulta).toHaveBeenCalledTimes(1)
  })

  it("submits with Enter but preserves a Shift+Enter newline", async () => {
    const question = "¿Qué controles contiene el corpus normativo?"
    const { unmount } = render(<GraphRagQuery />)
    const textbox = screen.getByRole("textbox")
    await act(async () => {})

    fireEvent.change(textbox, { target: { value: question } })
    fireEvent.keyDown(textbox, { key: "Enter", shiftKey: false })
    await waitFor(() => expect(analizarConsulta).toHaveBeenCalledWith({ pregunta: question }))
    await waitFor(() => expect(screen.getByTestId("graph-result")).toBeInTheDocument())

    unmount()
    vi.clearAllMocks()
    analizarConsulta.mockResolvedValue(newResult)
    render(<GraphRagQuery />)
    await act(async () => {})
    const multilineTextbox = screen.getByRole("textbox")
    const multilineQuestion = "Primera línea de una pregunta válida\nSegunda línea"
    fireEvent.change(multilineTextbox, { target: { value: multilineQuestion } })
    fireEvent.keyDown(multilineTextbox, { key: "Enter", shiftKey: true })

    expect(multilineTextbox).toHaveValue(multilineQuestion)
    expect(analizarConsulta).not.toHaveBeenCalled()
  })

  it("rejects short questions without creating a transcript exchange", async () => {
    render(<GraphRagQuery />)
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "Muy corta" } })
    fireEvent.click(screen.getByRole("button", { name: "Enviar" }))

    expect(await screen.findByRole("alert")).toHaveTextContent("La pregunta debe tener al menos 20 caracteres.")
    expect(screen.queryByTestId("graph-result")).not.toBeInTheDocument()
    expect(screen.queryByText("Analizando el corpus…")).not.toBeInTheDocument()
    expect(analizarConsulta).not.toHaveBeenCalled()
  })

  it("preserves completed exchanges and restores the question after a POST error", async () => {
    const question = "¿Qué controles nuevos contiene el corpus normativo?"
    obtenerConsulta.mockResolvedValueOnce(savedResult)
    analizarConsulta.mockRejectedValueOnce(new Error("Servicio no disponible"))

    render(<GraphRagQuery initialConsultaId="query-1" />)
    await waitFor(() => expect(screen.getByTestId("graph-result")).toBeInTheDocument())
    fireEvent.change(screen.getByRole("textbox"), { target: { value: question } })
    fireEvent.click(screen.getByRole("button", { name: "Enviar" }))

    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Servicio no disponible"))
    expect(screen.getAllByTestId("graph-result")).toHaveLength(1)
    expect(screen.getByText("Respuesta persistida")).toBeInTheDocument()
    expect(screen.queryByText("Analizando el corpus…")).not.toBeInTheDocument()
    expect(screen.getByRole("textbox")).toHaveValue(question)
  })

  it("clears the transcript, composer, and error for Nueva conversación", async () => {
    const { rerender } = render(<GraphRagQuery initialConsultaId="query-1" />)
    await waitFor(() => expect(screen.getByTestId("graph-result")).toBeInTheDocument())

    fireEvent.change(screen.getByRole("textbox"), { target: { value: "Corta" } })
    fireEvent.click(screen.getByRole("button", { name: "Enviar" }))
    expect(screen.getByRole("alert")).toBeInTheDocument()

    fireEvent.click(screen.getByRole("button", { name: "Nueva conversación" }))

    expect(replace).toHaveBeenCalledWith("/consultar", { scroll: false })
    expect(screen.queryByTestId("graph-result")).not.toBeInTheDocument()
    expect(screen.queryByRole("alert")).not.toBeInTheDocument()
    expect(screen.getByRole("textbox")).toHaveValue("")

    rerender(<GraphRagQuery initialConsultaId={null} />)
    await waitFor(() => expect(screen.getByText("Escribe una pregunta sobre el corpus normativo para iniciar la conversación.")).toBeInTheDocument())
    expect(obtenerConsulta).toHaveBeenCalledTimes(1)
  })
})
