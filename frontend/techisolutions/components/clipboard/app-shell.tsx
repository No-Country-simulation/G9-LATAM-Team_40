"use client"

import { AppNav } from "@/components/clipboard/app-nav"
import { GlobalSearchProvider } from "@/components/clipboard/global-search-context"
import { SiteHeader } from "@/components/clipboard/site-header"
import { cn } from "@/lib/utils"

interface AppShellProps {
  currentPath: string
  children: React.ReactNode
  contentClassName?: string
}

export function AppShell({
  currentPath,
  children,
  contentClassName,
}: AppShellProps) {
  return (
    <GlobalSearchProvider>
      <div className="min-h-svh bg-background">
        <SiteHeader variant="app" />
        <AppNav currentPath={currentPath} />
        <main
          className={cn(
            "mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8",
            contentClassName
          )}
        >
          {children}
        </main>
      </div>
    </GlobalSearchProvider>
  )
}
