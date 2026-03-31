import type { FeedListResponse } from './types'
import type { BoardSort } from './boards'
import { apiFetch, authHeadersJson, getBaseUrl, parseJsonError } from './client'

export async function fetchFeed(params: {
  page?: number
  page_size?: number
  sort?: BoardSort
  /** 제목·설명·장소 검색 */
  q?: string
}): Promise<FeedListResponse> {
  const sp = new URLSearchParams()
  if (params.page) sp.set('page', String(params.page))
  if (params.page_size) sp.set('page_size', String(params.page_size))
  if (params.sort) sp.set('sort', params.sort)
  if (params.q?.trim()) sp.set('q', params.q.trim())
  const q = sp.toString()
  const res = await apiFetch(`${getBaseUrl()}/api/feed${q ? `?${q}` : ''}`, {
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as FeedListResponse
}
