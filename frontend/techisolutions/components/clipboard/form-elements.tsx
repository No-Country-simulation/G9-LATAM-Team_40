import { cn } from "@/lib/utils"

const CATEGORY_COLORS: Record<string, string> = {
  "Política SST": "bg-institutional text-primary-foreground",
  "Procedimientos": "bg-carbon text-primary-foreground",
  "Matrices de Riesgo": "bg-sst-yellow text-institutional",
  Registros: "bg-secondary text-institutional",
  Auditorías: "bg-stamp-red text-primary-foreground",
}

interface CategoryBadgeProps {
  category: string
  className?: string
}

export function CategoryBadge({ category, className }: CategoryBadgeProps) {
  const colorClass =
    CATEGORY_COLORS[category] ?? "bg-muted text-muted-foreground"

  return (
    <span
      className={cn(
        "inline-block border border-institutional/20 px-2 py-0.5 text-xs font-bold tracking-wide uppercase",
        colorClass,
        className
      )}
    >
      {category}
    </span>
  )
}

interface CheckCellProps {
  checked?: boolean
  number?: number
  label: string
  stepLabel?: string
  className?: string
}

export function CheckCell({
  checked = true,
  number,
  label,
  stepLabel,
  className,
}: CheckCellProps) {
  return (
    <div className={cn("flex items-start gap-3", className)}>
      <span
        className={cn(
          "flex size-8 shrink-0 items-center justify-center border-2 font-mono text-sm font-bold",
          checked
            ? "border-institutional bg-institutional text-primary-foreground"
            : "border-institutional bg-card text-institutional"
        )}
        aria-hidden
      >
        {checked ? "✓" : number}
      </span>
      <div className="min-w-0 pt-0.5">
        {stepLabel ? (
          <p className="mb-0.5 font-mono text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            {stepLabel}
          </p>
        ) : null}
        <span className="text-sm font-medium leading-snug text-foreground">
          {label}
        </span>
      </div>
    </div>
  )
}

interface FormPaperProps {
  children: React.ReactNode
  className?: string
  /** `plain` — sin líneas de cuaderno; ideal para bloques de lectura larga */
  variant?: "ruled" | "plain"
}

export function FormPaper({
  children,
  className,
  variant = "ruled",
}: FormPaperProps) {
  return (
    <div
      className={cn(
        "border-2 border-institutional bg-card shadow-[4px_4px_0_0_rgba(26,58,92,0.12)]",
        variant === "ruled" && "ruled-paper",
        className
      )}
    >
      {children}
    </div>
  )
}
