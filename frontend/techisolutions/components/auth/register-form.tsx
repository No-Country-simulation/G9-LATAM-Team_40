"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { Loader2 } from "lucide-react"

import { AuthShell } from "@/components/clipboard/auth-shell"
import { FormAlert, FormField } from "@/components/clipboard/form-field"
import { setAccessToken } from "@/lib/token"
import { register } from "@/services/auth.service"

export function RegisterForm() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [fieldErrors, setFieldErrors] = useState<{
    email?: string
    password?: string
    confirmPassword?: string
  }>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  function validate(): boolean {
    const errors: {
      email?: string
      password?: string
      confirmPassword?: string
    } = {}
    if (!email.trim()) {
      errors.email = "El correo es obligatorio."
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.email = "Ingresa un correo válido."
    }
    if (!password) {
      errors.password = "La contraseña es obligatoria."
    } else if (password.length < 8) {
      errors.password = "Usa al menos 8 caracteres."
    }
    if (!confirmPassword) {
      errors.confirmPassword = "Confirma tu contraseña."
    } else if (password !== confirmPassword) {
      errors.confirmPassword = "Las contraseñas no coinciden."
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
      const response = await register({ email: email.trim(), password })
      setAccessToken(response.access_token)
      router.push("/dashboard")
      router.refresh()
    } catch (err) {
      setFormError(
        err instanceof Error
          ? err.message
          : "No se pudo crear la cuenta. Intenta de nuevo."
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      formCode="Form. ALT-01"
      title="Crear cuenta"
      description="Registra un coordinador SST para consultar el corpus normativo y administrar un índice privado por usuario."
      footer={
        <>
          ¿Ya tienes cuenta?{" "}
          <Link
            href="/login"
            className="font-semibold text-institutional hover:underline"
          >
            Inicia sesión
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        {formError ? <FormAlert variant="error">{formError}</FormAlert> : null}

        <FormAlert variant="info">
          Cuenta de demostración para el hackathon. No inventes datos de clientes
          reales en el correo.
        </FormAlert>

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
          hint="Mínimo 8 caracteres."
          required
          autoComplete="new-password"
          disabled={loading}
        />

        <FormField
          id="confirmPassword"
          label="Confirmar contraseña"
          type="password"
          value={confirmPassword}
          onChange={setConfirmPassword}
          error={fieldErrors.confirmPassword}
          required
          autoComplete="new-password"
          disabled={loading}
        />

        <button
          type="submit"
          disabled={loading}
          className="stamp-shadow flex w-full items-center justify-center gap-2 border-2 border-institutional bg-institutional py-3 text-sm font-bold text-primary-foreground transition-transform hover:-translate-y-px disabled:translate-y-0 disabled:opacity-70"
        >
          {loading ? (
            <>
              <Loader2 className="size-4 animate-spin" aria-hidden />
              Creando cuenta…
            </>
          ) : (
            "Registrar y continuar"
          )}
        </button>
      </form>
    </AuthShell>
  )
}
