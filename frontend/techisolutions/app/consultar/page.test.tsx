import { describe, expect, it } from "vitest"

import ConsultarPage from "@/app/consultar/page"

describe("ConsultarPage", () => {
  it("passes a single persisted query id to GraphRagQuery", async () => {
    const page = await ConsultarPage({ searchParams: Promise.resolve({ consulta: "query-1" }) })

    expect(page).toEqual(expect.objectContaining({ props: { initialConsultaId: "query-1" } }))
  })

  it("uses the first id when consulta appears more than once", async () => {
    const page = await ConsultarPage({ searchParams: Promise.resolve({ consulta: ["query-1", "query-2"] }) })

    expect(page).toEqual(expect.objectContaining({ props: { initialConsultaId: "query-1" } }))
  })

  it("passes null when no persisted query id exists", async () => {
    const page = await ConsultarPage({ searchParams: Promise.resolve({}) })

    expect(page).toEqual(expect.objectContaining({ props: { initialConsultaId: null } }))
  })
})
