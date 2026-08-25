import Link from "next/link"

import { CategoryBadge } from "@/components/clipboard/form-elements"
import { cn } from "@/lib/utils"

interface RecentDocumentCardProps {
  titulo: string
  categoria: string
  relevancia: number
  palabras_clave: string[]
  procesado_en: string
  href: string
  className?: string
}

export function RecentDocumentCard({ titulo, categoria, relevancia, palabras_clave, procesado_en, href, className }: RecentDocumentCardProps) {
  const date = new Date(procesado_en).toLocaleDateString("es-CL", { day: "numeric", month: "short", year: "numeric" })
  return (
    <Link
      href={href}
      className="block focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-institutional"
    >
      <article className={cn("border-2 border-border bg-card p-4 transition-colors hover:border-institutional/50", className)}>
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <CategoryBadge category={categoria} />
          <span className="font-mono text-xs text-muted-foreground">{Math.round(relevancia * 100)}% relevancia</span>
        </div>
        <h3 className="mb-2 text-base font-semibold leading-snug text-institutional">{titulo}</h3>
        <div className="mb-3 flex flex-wrap gap-1.5">
          {palabras_clave.slice(0, 3).map((keyword) => (
            <span key={keyword} className="border border-border bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
              {keyword}
            </span>
          ))}
        </div>
        <p className="font-mono text-[11px] text-muted-foreground">Procesado: {date}</p>
      </article>
    </Link>
  )
}

interface StatCellProps {
  label: string
  value: number | string
  href?: string
}

export function StatCell({ label, value, href }: StatCellProps) {
  const content = <><span className="font-mono text-2xl font-bold tabular-nums text-institutional sm:text-3xl">{value}</span><span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</span></>
  if (href) return <Link href={href} className="flex flex-col gap-1 border-2 border-border bg-card p-4 transition-colors hover:border-institutional hover:bg-secondary/40">{content}</Link>
  return <div className="flex flex-col gap-1 border-2 border-border bg-card p-4">{content}</div>
}
