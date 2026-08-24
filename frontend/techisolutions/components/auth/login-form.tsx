"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { Loader2 } from "lucide-react"

import { AuthShell } from "@/components/clipboard/auth-shell"
import { FormAlert, FormField } from "@/components/clipboard/form-field"
import { setAccessToken } from "@/lib/token"
import { login } from "@/services/auth.service"

export function LoginForm() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [fieldErrors, setFieldErrors] = useState<{
    email?: string
    password?: string
  }>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  function validate(): boolean {
    const errors: { email?: string; password?: string } = {}
    if (!email.trim()) {
      errors.email = "El correo es obligatorio."
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.email = "Ingresa un correo válido."
    }
    if (!password) {
      errors.password = "La contraseña es obligatoria."
    }
    setFieldErrors(errors)
    return Object.keys(errors).length === 0
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setFormError(null)
    if (!validate()) return

    setLoading(true)
    try {
      const response = await login({ email: email.trim(), password })
      setAccessToken(response.access_token)
      router.push("/dashboard")
      router.refresh()
    } catch (err) {
      setFormError(
        err instanceof Error
          ? err.message
          : "Error al iniciar sesión. Intenta de nuevo."
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      formCode="Form. ACC-01"
      title="Iniciar sesión"
      description="Accede al análisis GraphRAG, administra tus archivos privados y revisa la evidencia de cada consulta."
      footer={
        <>
          ¿No tienes cuenta?{" "}
          <Link
            href="/register"
            className="font-semibold text-institutional hover:underline"
          >
            Regístrate aquí
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        {formError ? <FormAlert variant="error">{formError}</FormAlert> : null}

        <FormField
          id="email"
          label="Correo electrónico"
          type="email"
          value={email}
          onChange={setEmail}
          error={fieldErrors.email}
          required
          autoComplete="email"
          disabled={loading}
        />

        <FormField
          id="password"
          label="Contraseña"
          type="password"
          value={password}
          onChange={setPassword}
          error={fieldErrors.password}
          required
          autoComplete="current-password"
          disabled={loading}
        />

        <button
          type="submit"
          disabled={loading}
          className="stamp-shadow flex w-full items-center justify-center gap-2 border-2 border-institutional bg-sst-yellow py-3 text-sm font-bold text-institutional transition-transform hover:-translate-y-px disabled:translate-y-0 disabled:opacity-70"
        >
          {loading ? (
            <>
              <Loader2 className="size-4 animate-spin" aria-hidden />
              Verificando credenciales…
            </>
          ) : (
            "Entrar al panel"
          )}
        </button>
      </form>
    </AuthShell>
  )
}
