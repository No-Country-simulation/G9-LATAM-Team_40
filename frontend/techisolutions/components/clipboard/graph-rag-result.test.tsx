import { act, fireEvent, render, screen } from "@testing-library/react"
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
  it("shows relevance and corpus badges, downloading only private source", async () => {
    render(<GraphRagResult result={result} />)
    expect(screen.getAllByText(/Relevancia/).length).toBeGreaterThan(0)
    expect(screen.getByText("BASE")).toBeInTheDocument()
    expect(screen.getByText("PRIVADO")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Descargar fuente" })).toBeInTheDocument()
    expect(screen.queryByText(/oci:\/\//i)).not.toBeInTheDocument()

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Descargar fuente" }))
    })
    expect(download).toHaveBeenCalledWith("file-1", "Manual privado")
  })
})
