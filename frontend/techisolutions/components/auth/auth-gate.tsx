"use client"

import { useEffect, useSyncExternalStore } from "react"
import { useRouter } from "next/navigation"

import { getAccessToken } from "@/lib/token"

function subscribe() {
  return () => {}
}

function getSnapshot() {
  return Boolean(getAccessToken())
}

function getServerSnapshot() {
  return false
}

export function AuthGate({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const authed = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)

  useEffect(() => {
    if (!authed) {
      router.replace("/login")
    }
  }, [authed, router])

  if (!authed) {
    return (
      <div className="flex min-h-svh items-center justify-center bg-background">
        <p className="font-mono text-sm text-muted-foreground">
          Verificando sesión…
        </p>
      </div>
    )
  }

  return children
}
