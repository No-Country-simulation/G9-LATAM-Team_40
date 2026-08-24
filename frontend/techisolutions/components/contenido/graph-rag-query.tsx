"use client"

import { useState } from "react"
import { Loader2, Search } from "lucide-react"

import { AuthGate } from "@/components/auth/auth-gate"
import { AppShell } from "@/components/clipboard/app-shell"
import { FormPaper } from "@/components/clipboard/form-elements"
import { FormAlert } from "@/components/clipboard/form-field"
import { GraphRagResult } from "@/components/clipboard/graph-rag-result"
import { analizarConsulta } from "@/services/consulta.service"
import type { ConsultaResponse } from "@/types/consulta.types"

const MIN_QUESTION_LENGTH = 20

export function GraphRagQuery() {
  const [pregunta, setPregunta] = useState("")
  const [result, setResult] = useState<ConsultaResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const value = pregunta.trim()
    setError(null)
    setResult(null)
    if (value.length < MIN_QUESTION_LENGTH) {
      setError(`La pregunta debe tener al menos ${MIN_QUESTION_LENGTH} caracteres.`)
      return
    }
    setLoading(true)
    try {
      setResult(await analizarConsulta({ pregunta: value }))
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo procesar la consulta.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthGate>
      <AppShell currentPath="/consultar">
        <div className="mb-6">
          <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">Form. QRY-01</p>
          <h1 className="text-2xl font-bold text-institutional sm:text-3xl">Análisis GraphRAG</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            Formula una pregunta sobre el corpus normativo base y, si existe, tu índice privado. Cada consulta conserva respuesta y fuentes.
          </p>
        </div>
        <FormPaper className="mb-6 p-5 sm:p-6">
          <form onSubmit={(event) => void submit(event)} className="space-y-4" noValidate>
            {error ? <FormAlert variant="error">{error}</FormAlert> : null}
            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-institutional">Pregunta</span>
              <textarea
                value={pregunta}
                onChange={(event) => setPregunta(event.target.value)}
                rows={5}
                minLength={MIN_QUESTION_LENGTH}
                required
                disabled={loading}
                placeholder="¿Qué obligaciones de seguridad contiene el corpus normativo?"
                className="w-full border-2 border-border bg-paper px-3 py-3 text-sm leading-relaxed focus-visible:border-carbon focus-visible:outline-none"
              />
              <span className="mt-1 block font-mono text-[10px] text-muted-foreground">Mínimo {MIN_QUESTION_LENGTH} caracteres.</span>
            </label>
            <button
              type="submit"
              disabled={loading}
              className="stamp-shadow inline-flex items-center gap-2 border-2 border-institutional bg-sst-yellow px-5 py-2.5 text-sm font-bold text-institutional disabled:opacity-60"
            >
              {loading ? <Loader2 className="size-4 animate-spin" aria-hidden /> : <Search className="size-4" aria-hidden />}
              {loading ? "Analizando…" : "Consultar corpus"}
            </button>
          </form>
        </FormPaper>
        {result ? <GraphRagResult result={result} /> : null}
      </AppShell>
    </AuthGate>
  )
}
