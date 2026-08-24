import Link from "next/link"
import {
  ArrowRight,
  FileSearch,
  FolderOpen,
  Search,
  Upload,
} from "lucide-react"

import { SiteHeader } from "@/components/clipboard/site-header"
import {
  CategoryBadge,
  FormPaper,
} from "@/components/clipboard/form-elements"
import {
  ApprovalStamp,
  IsoMark,
} from "@/components/clipboard/iso-mark"
import { ChecklistCascade } from "@/components/clipboard/checklist-cascade"
import {
  DEMO_CLASSIFICATION,
  ISO_CATEGORIES,
} from "@/lib/demo-data"

const CHECKLIST_STEPS = [
  "Recibe documentos dispersos (políticas, matrices, registros)",
  "Formula una pregunta sobre el corpus normativo",
  "Recupera fuentes base y privadas con aislamiento",
  "Revisa categoría, relevancia y ruta jerárquica",
  "Descarga fuentes privadas desde el backend",
] as const

const CAPABILITIES = [
  {
    icon: FileSearch,
    title: "Análisis GraphRAG",
    body: "Consulta el corpus normativo y conserva la evidencia de cada respuesta.",
  },
  {
    icon: Upload,
    title: "Índice privado por usuario",
    body: "Sube PDF, TXT o MD y reconstruye tu corpus aislado.",
  },
  {
    icon: Search,
    title: "Búsqueda de consultas",
    body: "Encuentra análisis anteriores por pregunta, fuente o palabra clave.",
  },
] as const

export default function LandingPage() {
  return (
    <div className="min-h-svh bg-background">
      <SiteHeader />

      <main>
        {/* Hero: promesa + mini-demo GraphRAG */}
        <section className="overflow-x-clip border-b-2 border-institutional">
          <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-12">
            <FormPaper variant="plain" className="p-5 sm:p-8 lg:p-10">
              <div className="mb-5 flex flex-wrap items-center gap-3 border-b-2 border-institutional pb-4 sm:mb-6">
                <IsoMark size="sm" />
                <div className="flex min-w-0 flex-1 flex-wrap items-center gap-2 sm:gap-3">
                  <span className="tape-strip px-3 py-1 text-[10px] font-bold tracking-widest text-institutional uppercase">
                    ISO 45001 · SST
                  </span>
                  <span className="font-mono text-[10px] text-muted-foreground">
                    Form. SST-45001 · Rev. 01
                  </span>
                </div>
              </div>

              <div
                className="mb-6 flex flex-wrap gap-1.5 sm:mb-8"
                aria-label="Categorías normativas ISO 45001"
              >
                {ISO_CATEGORIES.map((cat) => (
                  <CategoryBadge key={cat} category={cat} />
                ))}
              </div>

              <div className="grid items-center gap-8 lg:grid-cols-2 lg:gap-10">
                <div>
                  <h1 className="mb-3 text-3xl font-bold leading-tight text-balance text-institutional sm:text-4xl lg:text-[2.5rem]">
                    Tu documentación ISO 45001, consultada y trazable
                  </h1>
                  <p className="mb-6 max-w-md text-sm leading-relaxed text-foreground sm:text-base">
                    Consulta el corpus normativo y conserva fuentes base o privadas con relevancia visible.
                  </p>

                  <div className="flex flex-wrap gap-3">
                    <Link
                      href="/register"
                      className="stamp-shadow inline-flex min-h-11 items-center gap-2 border-2 border-institutional bg-sst-yellow px-5 py-2.5 text-sm font-bold text-institutional transition-transform hover:-translate-y-px"
                    >
                      Crear cuenta
                      <ArrowRight className="size-4" aria-hidden />
                    </Link>
                    <Link
                      href="/login"
                      className="inline-flex min-h-11 items-center gap-2 border-2 border-institutional bg-card px-5 py-2.5 text-sm font-semibold text-institutional hover:bg-secondary/60"
                    >
                      Iniciar sesión
                    </Link>
                  </div>
                </div>

                <aside
                  className="overflow-visible border-2 border-institutional bg-background p-4 sm:p-5"
                  aria-label="Ejemplo de análisis GraphRAG"
                >
                  <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                    <p className="font-mono text-[10px] font-bold tracking-wider text-institutional uppercase">
                      Análisis GraphRAG
                    </p>
                    <span className="font-mono text-[10px] text-muted-foreground">
                      Datos de demostración
                    </span>
                  </div>

                  <p className="mb-1 font-mono text-[10px] font-bold tracking-wider text-muted-foreground uppercase">
                    Documento
                  </p>
                  <p className="mb-4 text-sm font-semibold text-institutional">
                    {DEMO_CLASSIFICATION.titulo}
                  </p>

                  <div className="mb-3 flex items-center gap-2" aria-hidden>
                    <span className="h-px flex-1 bg-border" />
                    <ArrowRight className="size-4 shrink-0 text-institutional/50" />
                    <span className="h-px flex-1 bg-border" />
                  </div>

                  <div className="relative overflow-visible border-2 border-stamp-red/40 bg-card p-3 sm:p-4">
                    <ApprovalStamp className="stamp-slam pointer-events-none absolute -top-2 right-0 size-14 opacity-90 sm:-top-4 sm:-right-2 sm:size-20" />
                    <div className="mb-3 flex flex-wrap items-center gap-2 pr-14 sm:pr-16">
                      <CategoryBadge
                        category={DEMO_CLASSIFICATION.categoria}
                      />
                      <span className="font-mono text-sm font-bold text-institutional">
                        {Math.round(DEMO_CLASSIFICATION.relevancia * 100)}%
                        relevancia
                      </span>
                    </div>
                    <p className="mb-2 text-xs font-medium text-foreground">
                      Palabras clave
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {DEMO_CLASSIFICATION.palabras_clave.map((kw) => (
                        <span
                          key={kw}
                          className="border border-institutional/30 bg-muted px-2 py-0.5 font-mono text-xs text-foreground"
                        >
                          {kw}
                        </span>
                      ))}
                    </div>
                  </div>
                </aside>
              </div>
            </FormPaper>
          </div>
        </section>

        {/* Checklist inspection steps — vertical sequence */}
        <section
          className="border-b-2 border-institutional bg-secondary/30"
          aria-labelledby="checklist-heading"
        >
          <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-14">
            <h2
              id="checklist-heading"
              className="mb-8 text-xl font-bold text-institutional sm:text-2xl"
            >
              Lista de verificación del proceso
            </h2>

            <FormPaper className="p-6 sm:p-8">
              <ChecklistCascade steps={CHECKLIST_STEPS} />
            </FormPaper>
          </div>
        </section>

        {/* Live demo: pasos 1 y 2 */}
        <section
          className="border-b-2 border-institutional"
          aria-labelledby="demo-heading"
        >
          <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-14">
            <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
              <div>
                <h2
                  id="demo-heading"
                  className="text-xl font-bold text-institutional sm:text-2xl"
                >
                  Así responde GraphRAG
                </h2>
                <p className="mt-1 max-w-2xl text-sm text-foreground">
                  Ejemplo estático de una consulta: fuentes normativas y palabras clave visibles.
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="tape-strip px-2 py-1 text-[10px] font-bold tracking-wider text-institutional uppercase">
                  Demo
                </span>
                <span className="font-mono text-[10px] text-muted-foreground">
                  Datos de demostración
                </span>
              </div>
            </div>

            <div className="grid gap-6 lg:grid-cols-[1fr_auto_1fr] lg:items-stretch lg:gap-4">
              <FormPaper variant="plain" className="p-5">
                <p className="mb-2 font-mono text-[10px] font-bold uppercase tracking-wider text-institutional">
                  Paso 1 — Recibe el documento
                </p>
                <p className="mb-2 text-sm font-semibold text-institutional">
                  {DEMO_CLASSIFICATION.titulo}
                </p>
                <p className="text-sm leading-relaxed text-foreground">
                  {DEMO_CLASSIFICATION.texto}
                </p>
              </FormPaper>

              <div
                className="hidden items-center justify-center lg:flex"
                aria-hidden
              >
                <ArrowRight className="size-6 text-institutional/50" />
              </div>

              <FormPaper className="border-stamp-red/40 p-5">
                <p className="mb-3 font-mono text-[10px] font-bold uppercase tracking-wider text-institutional">
                  Paso 2 — Respuesta y relevancia
                </p>
                <div className="mb-4 flex flex-wrap items-center gap-3">
                  <CategoryBadge category={DEMO_CLASSIFICATION.categoria} />
                  <span className="font-mono text-sm font-bold text-institutional">
                    {Math.round(DEMO_CLASSIFICATION.relevancia * 100)}%
                    relevancia
                  </span>
                </div>
                <p className="mb-2 text-xs font-medium text-foreground">
                  Palabras clave
                </p>
                <div className="flex flex-wrap gap-2">
                  {DEMO_CLASSIFICATION.palabras_clave.map((kw) => (
                    <span
                      key={kw}
                      className="border border-institutional/30 bg-muted px-2 py-0.5 font-mono text-xs"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              </FormPaper>
            </div>
          </div>
        </section>

        {/* Capabilities */}
        <section
          className="border-b-2 border-institutional bg-card"
          aria-labelledby="capabilities-heading"
        >
          <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-14">
            <h2
              id="capabilities-heading"
              className="mb-8 text-xl font-bold text-institutional sm:text-2xl"
            >
              Capacidades del sistema
            </h2>
            <div className="grid gap-4 md:grid-cols-3">
              {CAPABILITIES.map((cap) => (
                <div
                  key={cap.title}
                  className="border-2 border-border bg-background p-5"
                >
                  <cap.icon
                    className="mb-3 size-6 text-institutional"
                    aria-hidden
                  />
                  <h3 className="mb-2 font-bold text-institutional">
                    {cap.title}
                  </h3>
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {cap.body}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="bg-institutional text-primary-foreground">
          <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16">
            <div className="flex flex-col items-start gap-6 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="text-2xl font-bold sm:text-3xl">
                  Empieza tu registro documental
                </h2>
                <p className="mt-2 max-w-xl text-primary-foreground/85">
                  Consulta el corpus y revisa fuentes en el panel.
                </p>
              </div>
              <Link
                href="/register"
                className="stamp-shadow inline-flex items-center gap-2 border-2 border-primary-foreground bg-sst-yellow px-6 py-3 font-bold text-institutional transition-transform hover:-translate-y-px"
              >
                Registrarse gratis
                <ArrowRight className="size-4" aria-hidden />
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t-2 border-institutional bg-muted">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-6 text-sm text-muted-foreground sm:px-6 sm:flex-row sm:items-center sm:justify-between">
          <p>
            <span className="font-semibold text-institutional">
              TechISOlutions
            </span>
            · Hackathon ONE · Alura + Oracle
          </p>
          <p className="flex items-center gap-2 font-mono text-xs">
            <FolderOpen className="size-3.5" aria-hidden />
            G9-LATAM-Team_40
          </p>
        </div>
      </footer>
    </div>
  )
}
