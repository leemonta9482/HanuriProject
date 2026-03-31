import type {
  LoginPayload,
  LoginResponse,
  RegisterResponse,
  RegisterWithStudentCardPayload,
} from './types'
import { getBaseUrl, parseJsonError } from './client'

export async function registerUser(payload: RegisterWithStudentCardPayload): Promise<RegisterResponse> {
  const form = new FormData()
  form.append('user_id', payload.user_id.trim())
  form.append('password', payload.password)
  form.append('name', payload.name.trim())
  form.append('school_name', payload.school_name.trim())
  form.append('phone', payload.phone.trim())
  form.append('email', payload.email.trim())
  if (payload.student_id?.trim()) form.append('student_id', payload.student_id.trim())
  if (payload.interest_major?.trim()) form.append('interest_major', payload.interest_major.trim())
  form.append('student_id_card', payload.student_id_card)

  const res = await fetch(`${getBaseUrl()}/api/auth/register`, {
    method: 'POST',
    body: form,
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
