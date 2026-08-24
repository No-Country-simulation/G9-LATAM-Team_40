import type { ApiErrorBody } from "@/types/auth.types"
import { clearAccessToken, getAccessToken } from "@/lib/token"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080"

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message)
    this.name = "ApiError"
  }
}

async function parseError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as ApiErrorBody
    if (body.mensaje) return body.mensaje
    if (body.error) return body.error
    if (body.detail) return body.detail
  } catch {
    // ignore non-JSON error responses
  }
  return "No se pudo completar la solicitud."
}

async function fetchAuthenticated(path: string, options: RequestInit = {}): Promise<Response> {
  const token = getAccessToken()
  const headers = new Headers(options.headers)
  if (token) headers.set("Authorization", `Bearer ${token}`)
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json")
  }
  const response = await fetch(`${API_URL}${path}`, { ...options, headers })
  if (response.status === 401) {
    clearAccessToken()
    if (typeof window !== "undefined") window.location.href = "/login"
    throw new ApiError("Sesión expirada. Inicia sesión de nuevo.", 401)
  }
  if (!response.ok) throw new ApiError(await parseError(response), response.status)
  return response
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetchAuthenticated(path, options)
  if (response.status === 204 || response.headers.get("content-length") === "0") return undefined as T
  const contentType = response.headers.get("content-type") ?? ""
  if (!contentType.toLowerCase().includes("json")) return undefined as T
  return response.json() as Promise<T>
}

export async function apiFetchBlob(path: string, options: RequestInit = {}): Promise<Blob> {
  return (await fetchAuthenticated(path, options)).blob()
}
