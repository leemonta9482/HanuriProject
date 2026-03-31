import type {
  LoginPayload,
  LoginResponse,
  LoginUserInfo,
  RegisterResponse,
  RegisterWithStudentCardPayload,
  UserProfile,
} from './types'
import { apiFetch, authHeaders, authHeadersJson, createFetchAbortSignal, getBaseUrl, parseJsonError } from './client'

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

  const res = await apiFetch(`${getBaseUrl()}/api/auth/register`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as RegisterResponse
}

export async function loginUser(payload: LoginPayload): Promise<LoginResponse> {
  let res: Response
  try {
    res = await apiFetch(`${getBaseUrl()}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: createFetchAbortSignal(25_000),
    })
  } catch (e) {
    const name = e instanceof Error ? e.name : ''
    if (name === 'TimeoutError' || name === 'AbortError') {
      throw new Error(
        '서버에 연결할 수 없습니다. 백엔드가 실행 중인지, 주소(포트)가 맞는지 확인해 주세요.',
      )
    }
    throw e
  }
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as LoginResponse
}

export async function fetchCurrentUser(): Promise<LoginUserInfo> {
  const res = await apiFetch(`${getBaseUrl()}/api/auth/me`, {
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as LoginUserInfo
}

export async function fetchUserProfile(): Promise<UserProfile> {
  const res = await apiFetch(`${getBaseUrl()}/api/auth/me/profile`, {
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as UserProfile
}

export type UpdateProfilePayload = {
  phone: string
  interest_major: string | null
  profile_image?: File | null
  clear_profile_image?: boolean
}

export async function updateUserProfile(payload: UpdateProfilePayload): Promise<UserProfile> {
  const form = new FormData()
  form.append('phone', payload.phone.trim())
  form.append('interest_major', payload.interest_major?.trim() ?? '')
  if (payload.clear_profile_image) form.append('clear_profile_image', '1')
  if (payload.profile_image) form.append('profile_image', payload.profile_image)

  const res = await apiFetch(`${getBaseUrl()}/api/auth/me/profile`, {
    method: 'PATCH',
    headers: authHeaders(),
    body: form,
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as UserProfile
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  const res = await apiFetch(`${getBaseUrl()}/api/auth/me/password`, {
    method: 'POST',
    headers: authHeadersJson(),
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
}
