import { afterEach, describe, expect, it, vi } from "vitest"

import { obtenerIndice, reintentarIndice } from "@/services/indice.service"

afterEach(() => vi.unstubAllGlobals())

describe("indice service", () => {
  it("reads persisted status and requests retry through backend", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ estado: "FAILED", mensaje: "fallo", rebuild_pendiente: false }), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ estado: "DIRTY", mensaje: "reintento", rebuild_pendiente: true }), { status: 202, headers: { "Content-Type": "application/json" } }))
    vi.stubGlobal("fetch", fetchMock)

    expect((await obtenerIndice()).estado).toBe("FAILED")
    expect((await reintentarIndice()).estado).toBe("DIRTY")
    expect(fetchMock.mock.calls[1]?.[1]).toEqual(expect.objectContaining({ method: "POST" }))
  })
})
