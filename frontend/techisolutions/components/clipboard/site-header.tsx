import Link from "next/link"

import { GlobalSearch } from "@/components/clipboard/global-search"

interface SiteHeaderProps {
  variant?: "public" | "app" | "auth"
}

export function SiteHeader({ variant = "public" }: SiteHeaderProps) {
  return (
    <header className="border-b-2 border-institutional bg-card">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:flex-nowrap sm:gap-4 sm:px-6">
        <Link
          href={variant === "app" ? "/dashboard" : "/"}
          className="group flex shrink-0 items-center gap-2"
        >
          <span
            className="tape-strip -rotate-1 px-2 py-0.5 text-[10px] font-bold tracking-widest text-institutional uppercase"
            aria-hidden
          >
            ISO 45001
          </span>
          <span className="text-lg font-bold tracking-tight text-institutional sm:text-xl">
            TechISOlutions
          </span>
        </Link>

        {variant === "app" ? (
          <div className="order-3 w-full sm:order-none sm:w-auto sm:flex-1 sm:justify-center md:max-w-md lg:max-w-lg">
            <GlobalSearch />
          </div>
        ) : null}

        {variant === "public" ? (
          <nav className="flex items-center gap-2 sm:gap-3" aria-label="Cuenta">
            <Link
              href="/login"
              className="px-3 py-1.5 text-sm font-medium text-institutional underline-offset-4 hover:underline"
            >
              Iniciar sesión
            </Link>
            <Link
              href="/register"
              className="stamp-shadow border-2 border-institutional bg-institutional px-3 py-1.5 text-sm font-semibold text-primary-foreground transition-transform hover:-translate-y-px active:translate-y-0"
            >
              Registrarse
            </Link>
          </nav>
        ) : null}

        {variant === "auth" ? (
          <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
            Sesión segura
          </span>
        ) : null}

        {variant === "app" ? (
          <span className="hidden font-mono text-[10px] tracking-wider text-muted-foreground uppercase sm:inline">
            Búsqueda local
          </span>
        ) : null}
      </div>
    </header>
  )
}
