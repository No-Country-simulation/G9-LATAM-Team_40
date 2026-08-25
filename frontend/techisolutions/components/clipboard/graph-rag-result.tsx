"use client"

import { Bot, CircleUserRound, Download } from "lucide-react"
import { useState } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

import { CategoryBadge, FormPaper } from "@/components/clipboard/form-elements"
import { descargarArchivo } from "@/services/archivo.service"
import type { ConsultaResponse, TrazabilidadSeccion } from "@/types/consulta.types"

function percent(value: number): string {
  return `${Math.round(value * 100)}%`
}

function formatProcessedDate(value: string): string | null {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date.toLocaleString("es-CL")
}

function MarkdownResponse({ content }: { content: string }) {
  return (
    <div className="space-y-3 text-sm leading-relaxed text-foreground">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        allowedElements={[
          "a",
          "blockquote",
          "br",
          "code",
          "del",
          "em",
          "h1",
          "h2",
          "h3",
          "h4",
          "h5",
          "h6",
          "hr",
          "li",
          "ol",
          "p",
          "pre",
          "strong",
          "table",
          "tbody",
          "td",
          "tfoot",
          "th",
          "thead",
          "tr",
          "ul",
        ]}
        components={{
          h1: ({ children }) => <h1 className="border-b-2 border-institutional pb-1 text-base font-bold text-institutional">{children}</h1>,
          h2: ({ children }) => <h2 className="border-b border-institutional/40 pb-1 text-sm font-bold text-institutional">{children}</h2>,
          h3: ({ children }) => <h3 className="text-sm font-bold text-institutional">{children}</h3>,
          h4: ({ children }) => <h4 className="text-sm font-bold text-institutional">{children}</h4>,
          h5: ({ children }) => <h5 className="text-sm font-bold text-institutional">{children}</h5>,
          h6: ({ children }) => <h6 className="font-bold text-institutional">{children}</h6>,
          ul: ({ children }) => <ul className="list-disc space-y-1 pl-5">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal space-y-1 pl-5">{children}</ol>,
          li: ({ children }) => <li className="pl-1">{children}</li>,
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-sst-yellow bg-muted px-4 py-2 text-muted-foreground">{children}</blockquote>
          ),
          pre: ({ children }) => (
            <pre className="overflow-x-auto border-2 border-institutional bg-muted p-3 font-mono text-xs leading-relaxed">{children}</pre>
          ),
          code: ({ children, className }) => (
            <code className={`border border-institutional/20 bg-muted px-1.5 py-0.5 font-mono text-[0.9em] ${className ?? ""}`}>
              {children}
            </code>
          ),
          strong: ({ children }) => <strong className="font-bold text-institutional">{children}</strong>,
          em: ({ children }) => <em className="italic">{children}</em>,
          del: ({ children }) => <del className="text-muted-foreground">{children}</del>,
          a: ({ children, href }) => (
            <a href={href} target="_blank" rel="noreferrer" className="font-semibold text-institutional underline decoration-sst-yellow decoration-2 underline-offset-2">
              {children}
            </a>
          ),
          hr: () => <hr className="border-border" />,
          table: ({ children }) => (
            <div className="overflow-x-auto border border-border">
              <table className="min-w-full border-collapse text-left text-xs">{children}</table>
            </div>
          ),
          th: ({ children }) => <th className="border-b-2 border-institutional bg-muted px-3 py-2 font-bold text-institutional">{children}</th>,
          td: ({ children }) => <td className="border-b border-border px-3 py-2 align-top">{children}</td>,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
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
  const processedDate = formatProcessedDate(result.procesadoEn)

  return (
    <article className="space-y-4">
      <div className="flex justify-end">
        <div className="w-full max-w-[90%] border-2 border-institutional bg-institutional p-4 text-primary-foreground sm:max-w-[82%]">
          <div className="mb-2 flex items-center justify-end gap-2 font-mono text-xs font-bold tracking-wider uppercase">
            <span>Tú</span>
            <CircleUserRound className="size-4" aria-hidden />
          </div>
          <p className="whitespace-pre-wrap text-sm leading-relaxed">{result.pregunta}</p>
        </div>
      </div>

      <div className="flex justify-start">
        <FormPaper
          variant="plain"
          className="w-full max-w-[96%] border-l-4 border-l-sst-yellow p-5 sm:max-w-[90%] sm:p-6"
        >
          <div className="mb-4 flex flex-wrap items-center gap-2 border-b-2 border-institutional pb-3">
            <Bot className="size-5 text-institutional" aria-hidden />
            <p className="font-mono text-xs font-bold tracking-wider text-institutional uppercase">GraphRAG</p>
          </div>

          <div className="mb-5 flex flex-wrap items-center gap-2">
            <CategoryBadge category={result.categoriaFuentePrincipal || "Sin Categoría"} />
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-xs text-muted-foreground">
              <span>Relevancia principal {percent(result.relevancia)}</span>
              {result.tiempoSegundos != null ? <span>Duración {result.tiempoSegundos.toFixed(2)} s</span> : null}
              {processedDate ? <span>Procesado: {processedDate}</span> : null}
            </div>
          </div>

          <div className="mb-5">
            <p className="mb-2 text-xs font-medium text-muted-foreground">Respuesta</p>
            <MarkdownResponse content={result.respuesta || "No se recibió una respuesta."} />
          </div>

          {result.trazabilidad.length > 0 ? (
            <details className="border-t-2 border-border pt-3">
              <summary className="cursor-pointer font-mono text-xs font-bold text-institutional focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-institutional">
                Ver fuentes utilizadas ({result.trazabilidad.length})
              </summary>
              <ul className="mt-3 space-y-3">
                {result.trazabilidad.map((source, index) => (
                  <SourceCard key={`${source.corpus}-${source.documentoId}-${source.tituloSeccion}-${index}`} source={source} />
                ))}
              </ul>
            </details>
          ) : (
            <p className="border-t-2 border-border pt-3 text-sm text-muted-foreground">
              El modelo no devolvió trazabilidad para esta respuesta.
            </p>
          )}
        </FormPaper>
      </div>
    </article>
  )
}
