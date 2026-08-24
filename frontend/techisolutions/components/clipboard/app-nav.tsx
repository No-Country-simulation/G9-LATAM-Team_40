import Link from "next/link"
import { Files, LayoutDashboard, Network, Search } from "lucide-react"

import { LogoutLink } from "@/components/auth/logout-link"
import { cn } from "@/lib/utils"

const NAV_ITEMS = [
  { href: "/dashboard", label: "Panel", icon: LayoutDashboard },
  { href: "/consultar", label: "Consultar", icon: Search },
  { href: "/grafo", label: "Grafo", icon: Network },
  { href: "/archivos", label: "Archivos", icon: Files },
] as const

interface AppNavProps {
  currentPath?: string
}

export function AppNav({ currentPath = "/dashboard" }: AppNavProps) {
  return (
    <>
      <nav className="hidden border-b-2 border-institutional bg-sidebar md:block" aria-label="Principal">
        <div className="mx-auto flex max-w-6xl items-center gap-1 px-4 sm:px-6">
          {NAV_ITEMS.map((item) => {
            const active = currentPath === item.href
            return <Link key={item.href} href={item.href} className={cn("-mb-0.5 flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors", active ? "border-stamp-red text-institutional" : "border-transparent text-muted-foreground hover:border-border hover:text-institutional")}><item.icon className="size-4" aria-hidden />{item.label}</Link>
          })}
          <div className="ml-auto"><LogoutLink className="flex items-center gap-2 px-3 py-3 text-sm text-muted-foreground hover:text-stamp-red" /></div>
        </div>
      </nav>
      <nav className="flex gap-1 overflow-x-auto border-b-2 border-institutional bg-sidebar px-2 py-2 md:hidden" aria-label="Principal">
        {NAV_ITEMS.map((item) => {
          const active = currentPath === item.href
          return <Link key={item.href} href={item.href} className={cn("flex shrink-0 items-center gap-1.5 rounded-sm border px-3 py-2 text-xs font-medium", active ? "border-institutional bg-institutional text-primary-foreground" : "border-border bg-card text-muted-foreground")}><item.icon className="size-3.5" aria-hidden />{item.label}</Link>
        })}
      </nav>
    </>
  )
}
