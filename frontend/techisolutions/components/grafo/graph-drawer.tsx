"use client"

import {
  useEffect,
  useId,
  useRef,
  type ReactNode,
  type RefObject,
} from "react"

import styles from "@/components/grafo/graph-observatory.module.css"

export interface GraphDrawerProps {
  open: boolean
  side: "left" | "right"
  title: string
  triggerRef: RefObject<HTMLElement | null>
  onClose: () => void
  children: ReactNode
}

export function GraphDrawer({
  open,
  side,
  title,
  triggerRef,
  onClose,
  children,
}: GraphDrawerProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const closeRef = useRef<HTMLButtonElement>(null)
  const wasOpenRef = useRef(false)
  const headingId = useId()

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return

    if (open) {
      if (!dialog.open) dialog.showModal()
      wasOpenRef.current = true
      window.setTimeout(() => closeRef.current?.focus(), 0)
      return
    }

    if (dialog.open) dialog.close()
    if (wasOpenRef.current) {
      wasOpenRef.current = false
      triggerRef.current?.focus()
    }
  }, [open, triggerRef])

  function handleCancel(event: React.SyntheticEvent<HTMLDialogElement>) {
    event.preventDefault()
    onClose()
  }

  function handleNativeClose() {
    if (open) {
      onClose()
    } else if (wasOpenRef.current) {
      wasOpenRef.current = false
      triggerRef.current?.focus()
    }
  }

  return (
    <dialog
      ref={dialogRef}
      className={styles.drawer}
      data-side={side}
      aria-labelledby={headingId}
      onCancel={handleCancel}
      onClose={handleNativeClose}
    >
      <div className={styles.drawerContent}>
        <div className={styles.drawerHeader}>
          <h2 id={headingId} className="text-base font-bold text-institutional">
            {title}
          </h2>
          <button
            ref={closeRef}
            type="button"
            onClick={onClose}
            className={styles.closeButton}
          >
            Cerrar
          </button>
        </div>
        <div className={styles.drawerBody}>{children}</div>
      </div>
    </dialog>
  )
}
