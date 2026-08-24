import type { AuthRequest, AuthResponse } from "@/types/auth.types"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080"

async function parseError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { mensaje?: string; error?: string }
    if (body.mensaje) return body.mensaje
    if (body.error) return body.error
  } catch {
    // ignore
  }
  return "No se pudo completar la solicitud."
}

async function send(path: string, request: AuthRequest): Promise<AuthResponse> {
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  })
  if (!response.ok) throw new Error(await parseError(response))
  return response.json() as Promise<AuthResponse>
}

export async function login(request: AuthRequest): Promise<AuthResponse> {
  return send("/auth/login", request)
}

export async function register(request: AuthRequest): Promise<AuthResponse> {
  return send("/auth/register", request)
}
