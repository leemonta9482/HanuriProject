import type { LoginPayload, LoginResponse, RegisterPayload, RegisterResponse } from './types'

function getBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
}

async function parseJsonError(res: Response): Promise<string> {
  try {
    const data = (await res.json()) as { detail?: unknown }
    if (typeof data.detail === 'string') return data.detail
    if (Array.isArray(data.detail)) {
      return data.detail.map((d: { msg?: string }) => d.msg ?? '').filter(Boolean).join(' ')
    }
  } catch {
    /* ignore */
  }
  return `요청 실패 (${res.status})`
}

export async function registerUser(payload: RegisterPayload): Promise<RegisterResponse> {
  const res = await fetch(`${getBaseUrl()}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...payload,
      student_id: payload.student_id?.trim() || null,
      interest_major: payload.interest_major?.trim() || null,
    }),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as RegisterResponse
}

export async function loginUser(payload: LoginPayload): Promise<LoginResponse> {
  const res = await fetch(`${getBaseUrl()}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as LoginResponse
}
