export interface AuthRequest {
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  refresh_token?: string
  token_type?: string
  expires_in?: number
}

export interface ApiErrorBody {
  error?: string
  mensaje?: string
  detail?: string
}
