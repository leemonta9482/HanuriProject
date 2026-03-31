import type {
  BoardDetail,
  BoardListResponse,
  BoardStatus,
  BoardUpdatePayload,
  PurchaseRequest,
} from './types'
import { apiFetch, authHeaders, authHeadersJson, getBaseUrl, parseJsonError } from './client'

export type BoardSort = 'latest' | 'price_asc' | 'price_desc'

export async function fetchBoards(params: {
  page?: number
  page_size?: number
  sort?: BoardSort
  status?: string
}): Promise<BoardListResponse> {
  const sp = new URLSearchParams()
  if (params.page) sp.set('page', String(params.page))
  if (params.page_size) sp.set('page_size', String(params.page_size))
  if (params.sort) sp.set('sort', params.sort)
  if (params.status) sp.set('status', params.status)
  const q = sp.toString()
  const res = await apiFetch(`${getBaseUrl()}/api/boards${q ? `?${q}` : ''}`, {
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as BoardListResponse
}

export async function fetchBoard(id: number): Promise<BoardDetail> {
  const res = await apiFetch(`${getBaseUrl()}/api/boards/${id}`, {
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as BoardDetail
}

export async function createBoard(form: FormData): Promise<BoardDetail> {
  const res = await apiFetch(`${getBaseUrl()}/api/boards`, {
    method: 'POST',
    headers: authHeaders(),
    body: form,
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as BoardDetail
}

export async function updateBoard(id: number, body: BoardUpdatePayload): Promise<BoardDetail> {
  const res = await apiFetch(`${getBaseUrl()}/api/boards/${id}`, {
    method: 'PATCH',
    headers: authHeadersJson(),
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as BoardDetail
}

export async function updateBoardStatus(id: number, status: BoardStatus): Promise<BoardDetail> {
  const res = await apiFetch(`${getBaseUrl()}/api/boards/${id}/status`, {
    method: 'PATCH',
    headers: authHeadersJson(),
    body: JSON.stringify({ status }),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as BoardDetail
}

export async function deleteBoard(id: number): Promise<void> {
  const res = await apiFetch(`${getBaseUrl()}/api/boards/${id}`, {
    method: 'DELETE',
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
}

export async function addBoardImages(id: number, files: File[]): Promise<BoardDetail> {
  const fd = new FormData()
  for (const f of files) fd.append('files', f)
  const res = await apiFetch(`${getBaseUrl()}/api/boards/${id}/images`, {
    method: 'POST',
    headers: authHeaders(),
    body: fd,
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as BoardDetail
}

export async function deleteBoardImage(boardId: number, imageId: number): Promise<BoardDetail> {
  const res = await apiFetch(`${getBaseUrl()}/api/boards/${boardId}/images/${imageId}`, {
    method: 'DELETE',
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as BoardDetail
}

export async function addFavorite(boardId: number): Promise<BoardDetail> {
  const res = await apiFetch(`${getBaseUrl()}/api/boards/${boardId}/favorite`, {
    method: 'POST',
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as BoardDetail
}

export async function removeFavorite(boardId: number): Promise<BoardDetail> {
  const res = await apiFetch(`${getBaseUrl()}/api/boards/${boardId}/favorite`, {
    method: 'DELETE',
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as BoardDetail
}

export async function fetchMyFavorites(page = 1, page_size = 12): Promise<BoardListResponse> {
  const sp = new URLSearchParams({ page: String(page), page_size: String(page_size) })
  const res = await apiFetch(`${getBaseUrl()}/api/me/favorites?${sp}`, {
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as BoardListResponse
}

export async function createPurchaseRequest(boardId: number): Promise<PurchaseRequest> {
  const res = await apiFetch(`${getBaseUrl()}/api/boards/${boardId}/purchase-requests`, {
    method: 'POST',
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as PurchaseRequest
}

export async function fetchPurchaseRequests(boardId: number): Promise<PurchaseRequest[]> {
  const res = await apiFetch(`${getBaseUrl()}/api/boards/${boardId}/purchase-requests`, {
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as PurchaseRequest[]
}

export async function updatePurchaseRequest(
  requestId: number,
  status: 'ACCEPTED' | 'REJECTED',
): Promise<PurchaseRequest> {
  const res = await apiFetch(`${getBaseUrl()}/api/purchase-requests/${requestId}`, {
    method: 'PATCH',
    headers: authHeadersJson(),
    body: JSON.stringify({ status }),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as PurchaseRequest
}

export async function reportBoard(boardId: number, reason: string): Promise<void> {
  const res = await apiFetch(`${getBaseUrl()}/api/boards/${boardId}/reports`, {
    method: 'POST',
    headers: authHeadersJson(),
    body: JSON.stringify({ reason }),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
}
