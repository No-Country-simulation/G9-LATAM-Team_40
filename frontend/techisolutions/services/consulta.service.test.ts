import { afterEach, describe, expect, it, vi } from "vitest"

import { analizarConsulta } from "@/services/consulta.service"

afterEach(() => vi.unstubAllGlobals())

describe("consulta service", () => {
  it("posts one question to Spring with snake case response mapping", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      id: "query-1",
      pregunta: "¿Qué obligaciones contiene el corpus normativo?",
      respuesta: "Respuesta",
      categoria_fuente_principal: "Seguridad",
      relevancia: 0.8,
      palabras_clave: [],
      trazabilidad: [],
      tiempo_segundos: 1,
      procesado_en: "2026-08-24T10:00:00Z",
    }), { status: 200, headers: { "Content-Type": "application/json" } }))
    vi.stubGlobal("fetch", fetchMock)

    const response = await analizarConsulta({ pregunta: "¿Qué obligaciones contiene el corpus normativo?" })

    expect(response.relevancia).toBe(0.8)
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/api/consultas"), expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ pregunta: "¿Qué obligaciones contiene el corpus normativo?" }),
    }))
  })
})
