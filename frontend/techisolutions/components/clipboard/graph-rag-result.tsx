"use client"

import { Download, ExternalLink } from "lucide-react"
import { useState } from "react"

import { CategoryBadge, FormPaper } from "@/components/clipboard/form-elements"
import { descargarArchivo } from "@/services/archivo.service"
import type { ConsultaResponse, TrazabilidadSeccion } from "@/types/consulta.types"

function percent(value: number): string {
  return `${Math.round(value * 100)}%`
}

function SourceCard({ source }: { source: TrazabilidadSeccion }) {
  const [downloading, setDownloading] = useState(false)
  const canDownload = source.corpus === "PRIVADO" && Boolean(source.archivoId)

  async function handleDownload() {
    if (!source.archivoId) return
    setDownloading(true)
    try {
      await descargarArchivo(source.archivoId, source.documentoTitulo || "fuente")
    } finally {
      setDownloading(false)
    }
  }

  return (
    <li className="border-2 border-border bg-card p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <span className={`border px-2 py-0.5 font-mono text-[10px] font-bold tracking-wider uppercase ${source.corpus === "PRIVADO" ? "border-stamp-red/60 text-stamp-red" : "border-institutional/50 text-institutional"}`}>
          {source.corpus}
        </span>
        <span className="font-mono text-xs font-bold text-institutional">
          Relevancia {percent(source.relevancia)}
        </span>
      </div>
      <p className="mb-1 text-sm font-bold text-institutional">{source.documentoTitulo}</p>
      <p className="mb-2 text-xs text-foreground">{source.tituloSeccion}</p>
      {source.rutaJerarquica.length > 0 ? (
        <p className="mb-2 font-mono text-[10px] text-muted-foreground">
          Ruta: {source.rutaJerarquica.join(" > ")}
        </p>
      ) : null}
      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        {source.dominio ? <span>Dominio: {source.dominio}</span> : null}
        <CategoryBadge category={source.categoria || "Sin Categoría"} />
        <span>Nivel {source.nivel}</span>
      </div>
      {source.palabrasClave.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {source.palabrasClave.map((keyword) => (
            <span key={keyword} className="border border-institutional/20 bg-muted px-2 py-0.5 font-mono text-[10px]">
              {keyword}
            </span>
          ))}
        </div>
      ) : null}
      {canDownload ? (
        <button
          type="button"
          onClick={() => void handleDownload()}
          disabled={downloading}
          className="mt-4 inline-flex items-center gap-2 border-2 border-institutional px-3 py-1.5 text-xs font-semibold text-institutional disabled:opacity-50"
        >
          <Download className="size-3.5" aria-hidden />
          {downloading ? "Descargando…" : "Descargar fuente"}
        </button>
      ) : null}
    </li>
  )
}

export function GraphRagResult({ result }: { result: ConsultaResponse }) {
  return (
    <FormPaper className="p-5 sm:p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b-2 border-institutional pb-3">
        <div>
          <p className="font-mono text-[10px] font-bold tracking-wider text-muted-foreground uppercase">Análisis GraphRAG</p>
          <p className="mt-1 text-sm font-semibold text-institutional">{result.categoriaFuentePrincipal}</p>
        </div>
        <div className="text-right font-mono text-xs text-muted-foreground">
          <p>Relevancia principal {percent(result.relevancia)}</p>
          {result.tiempoSegundos != null ? <p>{result.tiempoSegundos.toFixed(2)} s</p> : null}
        </div>
      </div>
      <div className="mb-5">
        <p className="mb-2 text-xs font-medium text-muted-foreground">Respuesta del modelo</p>
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">{result.respuesta || "No se recibió una respuesta."}</p>
      </div>
      {result.trazabilidad.length > 0 ? (
        <div>
          <div className="mb-2 flex items-center justify-between gap-3">
            <p className="text-xs font-medium text-muted-foreground">Fuentes utilizadas</p>
            <ExternalLink className="size-3.5 text-muted-foreground" aria-hidden />
          </div>
          <ul className="space-y-3">
            {result.trazabilidad.map((source, index) => (
              <SourceCard key={`${source.corpus}-${source.documentoId}-${source.tituloSeccion}-${index}`} source={source} />
            ))}
          </ul>
        </div>
      ) : (
        <p className="border border-dashed border-border p-4 text-sm text-muted-foreground">
          El modelo no devolvió trazabilidad para esta respuesta.
        </p>
      )}
    </FormPaper>
  )
}
