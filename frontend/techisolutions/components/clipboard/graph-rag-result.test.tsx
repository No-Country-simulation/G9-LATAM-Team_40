import { act, fireEvent, render, screen, within } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import type { ConsultaResponse } from "@/types/consulta.types"

const { download } = vi.hoisted(() => ({ download: vi.fn() }))
vi.mock("@/services/archivo.service", () => ({ descargarArchivo: download }))

import { GraphRagResult } from "@/components/clipboard/graph-rag-result"

const result: ConsultaResponse = {
  id: "query-1",
  pregunta: "¿Qué obligaciones contiene el corpus normativo?",
  respuesta: "Respuesta GraphRAG",
  categoriaFuentePrincipal: "Seguridad",
  relevancia: 0.9,
  palabrasClave: ["riesgo"],
  tiempoSegundos: 1.5,
  procesadoEn: "2026-08-24T10:00:00Z",
  trazabilidad: [
    {
      documentoId: "base-doc",
      documentoTitulo: "Manual base",
      categoria: "Seguridad",
      palabrasClave: ["riesgo"],
      tituloSeccion: "Obligaciones base",
      rutaJerarquica: ["Capítulo 1"],
      nivel: 1,
      dominio: "ISOs",
      relevancia: 0.9,
      corpus: "BASE",
    },
    {
      documentoId: "private-doc",
      documentoTitulo: "Manual privado",
      categoria: "Privado",
      palabrasClave: [],
      tituloSeccion: "Procedimiento ACME",
      rutaJerarquica: [],
      nivel: 1,
      dominio: "LEYES",
      relevancia: 0.88,
      corpus: "PRIVADO",
      archivoId: "file-1",
    },
  ],
}

describe("GraphRagResult", () => {
  it("renders a conversation exchange with metadata and collapsed sources", async () => {
    render(<GraphRagResult result={result} />)

    expect(screen.getByText("Tú")).toBeInTheDocument()
    expect(screen.getByText("GraphRAG")).toBeInTheDocument()
    expect(screen.getByText(result.pregunta)).toBeInTheDocument()
    expect(screen.getByText("Respuesta GraphRAG")).toBeInTheDocument()
    expect(screen.getAllByText("Seguridad")).toHaveLength(2)
    expect(screen.getByText("Relevancia principal 90%")).toBeInTheDocument()
    expect(screen.getByText("Duración 1.50 s")).toBeInTheDocument()
    expect(screen.getByText(`Procesado: ${new Date(result.procesadoEn).toLocaleString("es-CL")}`)).toBeInTheDocument()

    const details = screen.getByText("Ver fuentes utilizadas (2)").closest("details")
    expect(details).not.toHaveAttribute("open")

    fireEvent.click(screen.getByText("Ver fuentes utilizadas (2)"))

    expect(details).toHaveAttribute("open")
    expect(within(details!).getByText("Manual base")).toBeInTheDocument()
    expect(within(details!).getByText("Manual privado")).toBeInTheDocument()
    expect(within(details!).getAllByRole("button", { name: "Descargar fuente" })).toHaveLength(1)

    await act(async () => {
      fireEvent.click(within(details!).getByRole("button", { name: "Descargar fuente" }))
    })
    expect(download).toHaveBeenCalledWith("file-1", "Manual privado")
  })
  it("formats markdown response structure without rendering raw HTML", () => {
    const markdown = `# Resumen

**Importante**: revisar el control.

- Primer requisito
- Segundo requisito

| Campo | Valor |
| --- | --- |
| Nivel | Alto |

[Ver fuente](https://example.com/fuente)

<script>alert("no ejecutar")</script>`
    const { container } = render(<GraphRagResult result={{ ...result, respuesta: markdown }} />)

    expect(screen.getByRole("heading", { level: 1, name: "Resumen" })).toBeInTheDocument()
    expect(screen.getByText("Importante", { selector: "strong" })).toBeInTheDocument()
    expect(screen.getAllByRole("list")).toHaveLength(2)
    expect(screen.getByRole("table")).toBeInTheDocument()
    expect(screen.getByRole("link", { name: "Ver fuente" })).toHaveAttribute("href", "https://example.com/fuente")
    expect(container.querySelector("script")).not.toBeInTheDocument()
  })


  it("shows the exact response fallback and no source disclosure when traceability is empty", () => {
    render(<GraphRagResult result={{ ...result, respuesta: "", trazabilidad: [] }} />)

    expect(screen.getByText("No se recibió una respuesta.")).toBeInTheDocument()
    expect(screen.getByText("El modelo no devolvió trazabilidad para esta respuesta.")).toBeInTheDocument()
    expect(screen.queryByText(/Ver fuentes utilizadas/)).not.toBeInTheDocument()
  })

  it("omits an invalid processed date instead of rendering Invalid Date", () => {
    render(<GraphRagResult result={{ ...result, procesadoEn: "not-a-date" }} />)

    expect(screen.queryByText(/Invalid Date/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Procesado:/)).not.toBeInTheDocument()
  })
})
