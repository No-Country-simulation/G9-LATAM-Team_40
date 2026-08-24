"use client"

import Link from "next/link"
import { LogOut } from "lucide-react"

import { clearAccessToken } from "@/lib/token"

export function LogoutLink({ className }: { className?: string }) {
  return (
    <Link
      href="/login"
      className={className}
      onClick={() => clearAccessToken()}
    >
      <LogOut className="size-4" aria-hidden />
      Salir
    </Link>
  )
}
