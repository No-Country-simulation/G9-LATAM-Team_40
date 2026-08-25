import type { ReactNode } from "react"

import { render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: { children: ReactNode; href: string }) => <a href={href} {...props}>{children}</a>,
}))

import { RecentDocumentCard } from "@/components/clipboard/document-card"

describe("RecentDocumentCard", () => {
  it("renders the complete analysis card as a keyboard-accessible link", () => {
    render(
      <RecentDocumentCard
        titulo="Pregunta persistida"
        categoria="Seguridad"
        relevancia={0.9}
        palabras_clave={["riesgo"]}
        procesado_en="2026-08-24T10:00:00Z"
        href="/consultar?consulta=query-1"
      />,
    )

    const link = screen.getByRole("link")
    expect(link).toHaveAttribute("href", "/consultar?consulta=query-1")
    expect(link).toHaveTextContent("Pregunta persistida")
    expect(link).toHaveTextContent("Seguridad")
    expect(link).toHaveAttribute("class", expect.stringContaining("focus-visible:outline"))
  })
})
