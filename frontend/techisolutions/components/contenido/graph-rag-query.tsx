"use client"

import { useEffect, useRef, useState } from "react"
import { useRouter } from "next/navigation"
import { Bot, CircleUserRound, Loader2, SendHorizontal } from "lucide-react"

import { AuthGate } from "@/components/auth/auth-gate"
import { AppShell } from "@/components/clipboard/app-shell"
import { FormPaper } from "@/components/clipboard/form-elements"
import { FormAlert } from "@/components/clipboard/form-field"
import { GraphRagResult } from "@/components/clipboard/graph-rag-result"
import { analizarConsulta, obtenerConsulta } from "@/services/consulta.service"

import type { ConsultaResponse } from "@/types/consulta.types"

const MIN_QUESTION_LENGTH = 20
const SAVED_QUERY_ERROR = "No se pudo abrir la consulta guardada."

type GraphRagQueryProps = {
  initialConsultaId?: string | null
}

export function GraphRagQuery({ initialConsultaId }: GraphRagQueryProps) {
  const router = useRouter()
  const [pregunta, setPregunta] = useState("")
  const [results, setResults] = useState<ConsultaResponse[]>([])
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadingSaved, setLoadingSaved] = useState(() => Boolean(initialConsultaId))
  const loadedConsultaIdRef = useRef<string | null>(null)
  const loadRequestRef = useRef(0)
  const transcriptEndRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const requestId = ++loadRequestRef.current
    let active = true

    if (!initialConsultaId) {
      queueMicrotask(() => {
        if (!active || requestId !== loadRequestRef.current) return
        setPregunta("")
        setResults([])
        setPendingQuestion(null)
        setError(null)
        setLoadingSaved(false)
        loadedConsultaIdRef.current = null
      })
      return () => {
        active = false
      }
    }

    if (loadedConsultaIdRef.current === initialConsultaId) return

    queueMicrotask(() => {
      if (!active || requestId !== loadRequestRef.current) return
      setLoadingSaved(true)
      setPregunta("")
      setResults([])
      setPendingQuestion(null)
      setError(null)
    })

    void obtenerConsulta(initialConsultaId)
      .then((response) => {
        if (!active || requestId !== loadRequestRef.current) return
        setPregunta("")
        setResults([response])
        setPendingQuestion(null)
        loadedConsultaIdRef.current = initialConsultaId
      })
      .catch((err: unknown) => {
        if (!active || requestId !== loadRequestRef.current) return
        loadedConsultaIdRef.current = null
        setPregunta("")
        setResults([])
        setPendingQuestion(null)
        setError(err instanceof Error && err.message ? err.message : SAVED_QUERY_ERROR)
      })
      .finally(() => {
        if (active && requestId === loadRequestRef.current) setLoadingSaved(false)
      })

    return () => {
      active = false
    }
  }, [initialConsultaId])

  useEffect(() => {
    const transcriptEnd = transcriptEndRef.current
    if (transcriptEnd && typeof transcriptEnd.scrollIntoView === "function") {
      transcriptEnd.scrollIntoView({ block: "end" })
    }
  }, [results, pendingQuestion])

  function startNewQuery() {
    loadRequestRef.current += 1
    loadedConsultaIdRef.current = null
    setPregunta("")
    setResults([])
    setPendingQuestion(null)
    setError(null)
    setLoading(false)
    setLoadingSaved(false)
    router.replace("/consultar", { scroll: false })
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (busy) return
    const value = pregunta.trim()
    setError(null)
    if (value.length < MIN_QUESTION_LENGTH) {
      setError(`La pregunta debe tener al menos ${MIN_QUESTION_LENGTH} caracteres.`)
      return
    }

    setLoading(true)
    setPendingQuestion(value)
    setPregunta("")
    try {
      const response = await analizarConsulta({ pregunta: value })
      setResults((current) => [...current, response])
      setPendingQuestion(null)
      loadedConsultaIdRef.current = response.id
      router.replace(`/consultar?consulta=${encodeURIComponent(response.id)}`, { scroll: false })
    } catch (err) {
      setPendingQuestion(null)
      setPregunta(value)
      setError(err instanceof Error && err.message ? err.message : "No se pudo procesar la consulta.")
    } finally {
      setLoading(false)
    }
  }

  function handleQuestionKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key !== "Enter" || event.shiftKey) return
    event.preventDefault()
    event.currentTarget.form?.requestSubmit()
  }

  const busy = loadingSaved || loading
  const showNewConversation = Boolean(initialConsultaId) || results.length > 0

  return (
    <AuthGate>
      <AppShell currentPath="/consultar" contentClassName="max-w-4xl py-4 sm:py-6">
        <div className="flex min-h-[calc(100svh-12rem)] flex-col">
          <header className="mb-5 flex flex-wrap items-end justify-between gap-4 border-b-2 border-institutional pb-4">
            <div>
              <p className="font-mono text-xs tracking-wider text-muted-foreground uppercase">Canal QRY-01</p>
              <h1 className="mt-1 text-2xl font-bold text-institutional sm:text-3xl">Chat GraphRAG</h1>
              <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
                Pregunta al corpus normativo y revisa la evidencia de cada respuesta.
              </p>
            </div>
            {showNewConversation ? (
              <button
                type="button"
                onClick={startNewQuery}
                disabled={busy}
                className="border-2 border-institutional px-3 py-2 text-sm font-semibold text-institutional underline-offset-4 hover:bg-muted hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-institutional disabled:cursor-not-allowed disabled:opacity-50"
              >
                Nueva conversación
              </button>
            ) : null}
          </header>

          <section
            role="log"
            aria-live="polite"
            aria-relevant="additions"
            aria-label="Conversación GraphRAG"
            aria-busy={busy}
            className="flex-1 space-y-6"
          >
            {results.length === 0 && !loadingSaved && !loading && !error && !pendingQuestion ? (
              <div className="flex justify-start">
                <FormPaper variant="plain" className="w-full max-w-[96%] border-l-4 border-l-sst-yellow p-4 sm:max-w-[90%] sm:p-5">
                  <div className="mb-2 flex items-center gap-2 font-mono text-xs font-bold tracking-wider text-institutional uppercase">
                    <Bot className="size-4" aria-hidden />
                    <span>GraphRAG</span>
                  </div>
                  <p className="text-sm leading-relaxed text-foreground">
                    Escribe una pregunta sobre el corpus normativo para iniciar la conversación.
                  </p>
                </FormPaper>
              </div>
            ) : null}

            {loadingSaved && results.length === 0 ? (
              <div className="flex justify-start">
                <FormPaper variant="plain" className="w-full max-w-[96%] border-l-4 border-l-sst-yellow p-4 sm:max-w-[90%] sm:p-5">
                  <div className="flex items-center gap-2 font-mono text-xs font-bold tracking-wider text-institutional uppercase">
                    <Loader2 className="size-4 animate-spin" aria-hidden />
                    <Bot className="size-4" aria-hidden />
                    <span>GraphRAG</span>
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">Cargando consulta guardada…</p>
                </FormPaper>
              </div>
            ) : null}

            {results.map((result) => (
              <GraphRagResult key={result.id} result={result} />
            ))}

            {pendingQuestion ? (
              <div className="space-y-4">
                <div className="flex justify-end">
                  <div className="w-full max-w-[90%] border-2 border-institutional bg-institutional p-4 text-primary-foreground sm:max-w-[82%]">
                    <div className="mb-2 flex items-center justify-end gap-2 font-mono text-xs font-bold tracking-wider uppercase">
                      <span>Tú</span>
                      <CircleUserRound className="size-4" aria-hidden />
                    </div>
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">{pendingQuestion}</p>
                  </div>
                </div>
                {loading ? (
                  <div className="flex justify-start">
                    <FormPaper variant="plain" className="w-full max-w-[96%] border-l-4 border-l-sst-yellow p-4 sm:max-w-[90%] sm:p-5">
                      <div className="flex items-center gap-2 font-mono text-xs font-bold tracking-wider text-institutional uppercase">
                        <Loader2 className="size-4 animate-spin" aria-hidden />
                        <Bot className="size-4" aria-hidden />
                        <span>GraphRAG</span>
                      </div>
                      <p className="mt-2 text-sm text-muted-foreground">Analizando el corpus…</p>
                    </FormPaper>
                  </div>
                ) : null}
              </div>
            ) : null}

            <div ref={transcriptEndRef} aria-hidden />
          </section>

          <FormPaper variant="plain" className="sticky bottom-2 mt-5 p-4 sm:p-5">
            <form onSubmit={(event) => void submit(event)} className="space-y-3" noValidate>
              {error ? <FormAlert variant="error">{error}</FormAlert> : null}
              <div className="flex items-end gap-3">
                <label htmlFor="graph-rag-question" className="min-w-0 flex-1">
                  <span className="sr-only">Pregunta</span>
                  <textarea
                    id="graph-rag-question"
                    value={pregunta}
                    onChange={(event) => setPregunta(event.target.value)}
                    onKeyDown={handleQuestionKeyDown}
                    rows={2}
                    minLength={MIN_QUESTION_LENGTH}
                    required
                    disabled={busy}
                    placeholder="¿Qué obligaciones de seguridad contiene el corpus normativo?"
                    className="w-full resize-y border-2 border-border bg-paper px-3 py-3 text-sm leading-relaxed focus-visible:border-carbon focus-visible:outline-none"
                  />
                  <span className="mt-1 block font-mono text-[10px] text-muted-foreground">
                    Enter para enviar · Shift+Enter para salto de línea · mínimo 20 caracteres.
                  </span>
                </label>
                <button
                  type="submit"
                  disabled={busy}
                  className="stamp-shadow inline-flex shrink-0 items-center gap-2 border-2 border-institutional bg-sst-yellow px-4 py-2.5 text-sm font-bold text-institutional focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-institutional disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {busy ? <Loader2 className="size-4 animate-spin" aria-hidden /> : <SendHorizontal className="size-4" aria-hidden />}
                  Enviar
                </button>
              </div>
            </form>
          </FormPaper>
        </div>
      </AppShell>
    </AuthGate>
  )
}

