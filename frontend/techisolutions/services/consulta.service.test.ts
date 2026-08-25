import { afterEach, describe, expect, it, vi } from "vitest"

import { analizarConsulta, obtenerConsulta } from "@/services/consulta.service"

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

  it("gets a persisted query by encoded id and maps its response", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      id: "query/1",
      pregunta: "Pregunta persistida",
      respuesta: "Respuesta persistida",
      categoria_fuente_principal: "Seguridad",
      relevancia: 0.9,
      palabras_clave: ["riesgo"],
      trazabilidad: [],
      tiempo_segundos: 1.25,
      procesado_en: "2026-08-24T10:00:00Z",
    }), { status: 200, headers: { "Content-Type": "application/json" } }))
    vi.stubGlobal("fetch", fetchMock)

    const response = await obtenerConsulta("query/1")

    expect(response).toMatchObject({
      id: "query/1",
      pregunta: "Pregunta persistida",
      respuesta: "Respuesta persistida",
      categoriaFuentePrincipal: "Seguridad",
      palabrasClave: ["riesgo"],
    })
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/consultas/query%2F1"),
      expect.objectContaining({ method: "GET" }),
    )
  })
})
