import type { WantedListResponse, WantedPost, WantedPostPayload } from './types'
import { apiFetch, authHeadersJson, getBaseUrl, parseJsonError } from './client'

export async function fetchMyWanted(params?: {
  page?: number
  page_size?: number
}): Promise<WantedListResponse> {
  const sp = new URLSearchParams()
  if (params?.page) sp.set('page', String(params.page))
  if (params?.page_size) sp.set('page_size', String(params.page_size))
  const q = sp.toString()
  const res = await apiFetch(`${getBaseUrl()}/api/wanted/me${q ? `?${q}` : ''}`, {
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as WantedListResponse
}

export async function fetchWanted(id: number): Promise<WantedPost> {
  const res = await apiFetch(`${getBaseUrl()}/api/wanted/${id}`, {
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as WantedPost
}

export async function createWanted(body: WantedPostPayload): Promise<WantedPost> {
  const res = await apiFetch(`${getBaseUrl()}/api/wanted`, {
    method: 'POST',
    headers: authHeadersJson(),
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as WantedPost
}

export async function updateWanted(id: number, body: Partial<WantedPostPayload>): Promise<WantedPost> {
  const res = await apiFetch(`${getBaseUrl()}/api/wanted/${id}`, {
    method: 'PATCH',
    headers: authHeadersJson(),
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as WantedPost
}

export async function deleteWanted(id: number): Promise<void> {
  const res = await apiFetch(`${getBaseUrl()}/api/wanted/${id}`, {
    method: 'DELETE',
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
}
