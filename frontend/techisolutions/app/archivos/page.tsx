import { Suspense } from "react"

import { ArchivosPanel } from "@/components/archivos/archivos-panel"

export default function ArchivosPage() {
  return (
    <Suspense
      fallback={
        <p className="p-8 font-mono text-sm text-muted-foreground">
          Cargando repositorio…
        </p>
      }
    >
      <ArchivosPanel />
    </Suspense>
  )
}
