import { createRef } from "react"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { GraphDrawer } from "@/components/grafo/graph-drawer"

describe("GraphDrawer", () => {
  beforeEach(() => {
    Object.defineProperty(HTMLDialogElement.prototype, "showModal", {
      configurable: true,
      value() {
        this.setAttribute("open", "")
      },
    })
    Object.defineProperty(HTMLDialogElement.prototype, "close", {
      configurable: true,
      value() {
        this.removeAttribute("open")
      },
    })
    vi.spyOn(HTMLDialogElement.prototype, "showModal")
    vi.spyOn(HTMLDialogElement.prototype, "close")
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("opens, focuses close, handles cancel, and returns focus to trigger", async () => {
    const triggerRef = createRef<HTMLButtonElement>()
    const onClose = vi.fn()
    const { rerender } = render(
      <>
        <button ref={triggerRef} type="button">
          Explorar
        </button>
        <GraphDrawer
          open
          side="left"
          title="Categorías"
          triggerRef={triggerRef}
          onClose={onClose}
        >
          <p>Contenido</p>
        </GraphDrawer>
      </>
    )

    const dialog = screen.getByRole("dialog", { name: "Categorías" })
    expect(dialog).toHaveAttribute("open")
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Cerrar" })).toHaveFocus()
    )

    fireEvent(dialog, new Event("cancel", { bubbles: true, cancelable: true }))
    expect(onClose).toHaveBeenCalledTimes(1)

    rerender(
      <>
        <button ref={triggerRef} type="button">
          Explorar
        </button>
        <GraphDrawer
          open={false}
          side="left"
          title="Categorías"
          triggerRef={triggerRef}
          onClose={onClose}
        >
          <p>Contenido</p>
        </GraphDrawer>
      </>
    )
    await waitFor(() => expect(triggerRef.current).toHaveFocus())
  })
})
