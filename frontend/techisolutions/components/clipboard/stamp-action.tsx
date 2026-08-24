import Link from "next/link"
import type { LucideIcon } from "lucide-react"

import { cn } from "@/lib/utils"

interface StampActionProps {
  href: string
  icon: LucideIcon
  label: string
  description: string
  tone?: "default" | "yellow" | "red"
}

export function StampAction({
  href,
  icon: Icon,
  label,
  description,
  tone = "default",
}: StampActionProps) {
  return (
    <Link
      href={href}
      className={cn(
        "group stamp-shadow flex min-w-0 flex-1 flex-col gap-1 border-2 px-4 py-3 transition-transform hover:-translate-y-0.5 active:translate-y-0 sm:px-5 sm:py-4",
        tone === "yellow" &&
          "border-institutional bg-sst-yellow text-institutional",
        tone === "red" &&
          "border-stamp-red bg-stamp-red text-primary-foreground",
        tone === "default" &&
          "border-institutional bg-card text-institutional hover:bg-secondary/60"
      )}
    >
      <span className="flex items-center gap-2">
        <Icon className="size-5 shrink-0" aria-hidden />
        <span className="font-bold tracking-tight">{label}</span>
      </span>
      <span
        className={cn(
          "text-xs leading-snug",
          tone === "red" ? "text-primary-foreground/90" : "text-muted-foreground"
        )}
      >
        {description}
      </span>
    </Link>
  )
}

interface ClipboardClipBarProps {
  children: React.ReactNode
}

export function ClipboardClipBar({ children }: ClipboardClipBarProps) {
  return (
    <div className="relative">
      <div
        className="absolute left-1/2 top-0 z-10 h-3 w-24 -translate-x-1/2 -translate-y-1 rounded-sm bg-gradient-to-b from-[#8a8a8a] to-[#5a5a5a] shadow-md sm:w-32"
        aria-hidden
      />
      <div className="border-2 border-institutional bg-muted/50 pt-4">
        <div className="flex flex-col gap-2 p-3 sm:flex-row sm:gap-3 sm:p-4">
          {children}
        </div>
      </div>
    </div>
  )
}
