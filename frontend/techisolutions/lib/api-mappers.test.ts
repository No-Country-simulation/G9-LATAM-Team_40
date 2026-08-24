import { describe, expect, it } from "vitest"

import { mapArchivo, mapCategoria, mapConsulta } from "@/lib/api-mappers"

describe("API mappers", () => {
  it("maps snake case consultation traceability and score to relevance", () => {
    const result = mapConsulta({
      id: "query-1",
      pregunta: "¿Qué obligaciones contiene el corpus normativo?",
      respuesta: "Respuesta",
      categoria_fuente_principal: "Seguridad",
      relevancia: 0.91,
      palabras_clave: ["riesgo"],
      tiempo_segundos: 1.2,
      trazabilidad: [{
        documento_id: "doc-1",
        documento_titulo: "Manual",
        categoria: "Seguridad",
        palabras_clave: ["riesgo"],
        titulo_seccion: "Obligaciones",
        ruta_jerarquica: ["Capítulo 1"],
        nivel: 1,
        dominio: "ISOs",
        score: 0.91,
        corpus: "BASE",
        archivo_id: null,
        source_path: "/machine/private.pdf",
      }],
      procesado_en: "2026-08-24T10:00:00Z",
    })

    expect(result.relevancia).toBe(0.91)
    expect(result.trazabilidad[0]?.relevancia).toBe(0.91)
    expect(result.trazabilidad[0]?.corpus).toBe("BASE")
    expect(result.trazabilidad[0]).not.toHaveProperty("source_path")
  })

  it("maps files without exposing internal URLs", () => {
    const result = mapArchivo({
      id: "file-1",
      nombre: "manual.md",
      documento_id: "file-1__manual",
      dominio: "LEYES",
      tamano: 100,
      tipo: "text/markdown",
      subido_en: "2026-08-24T10:00:00Z",
      indexado_en: null,
      pendiente_eliminacion: false,
      url: "oci://private/object",
    })

    expect(result.dominio).toBe("LEYES")
    expect(result).not.toHaveProperty("url")
  })

  it("renames category counts to consultations", () => {
    expect(mapCategoria({ nombre: "Seguridad", total_consultas: 3 })).toEqual({
      nombre: "Seguridad",
      totalConsultas: 3,
    })
  })
})
