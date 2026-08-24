import { afterEach, describe, expect, it, vi } from "vitest"

import { descargarArchivo } from "@/services/archivo.service"

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

describe("archivo download service", () => {
  it("uses backend blob endpoint and never an OCI URL", async () => {
    vi.useFakeTimers()
    const fetchMock = vi.fn().mockResolvedValue(new Response("bytes", { status: 200 }))
    const createObjectURL = vi.fn().mockReturnValue("blob:test")
    const revokeObjectURL = vi.fn()
    vi.stubGlobal("fetch", fetchMock)
    vi.stubGlobal("URL", { createObjectURL, revokeObjectURL })
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined)

    await descargarArchivo("file-1", "manual.md")
    vi.runAllTimers()

    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/api/archivos/file-1/descarga"), expect.anything())
    expect(createObjectURL).toHaveBeenCalled()
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:test")
    expect(click).toHaveBeenCalled()
    click.mockRestore()
  })
})
