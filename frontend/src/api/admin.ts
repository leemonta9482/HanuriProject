import { apiFetch, authHeadersJson, getBaseUrl, parseJsonError } from './client'
import type {
  AdminBoard,
  AdminBoardListResponse,
  AdminBoardUpdatePayload,
  AdminReport,
  AdminReportListResponse,
  AdminReportUpdatePayload,
  AdminUser,
  AdminUserListResponse,
  AdminUserUpdatePayload,
} from './types'

export async function fetchAdminUsers(
  page: number,
  pageSize: number,
  filters?: { user_id?: string; name?: string; school_name?: string },
): Promise<AdminUserListResponse> {
  const q = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
  if (filters?.user_id?.trim()) q.set('user_id', filters.user_id.trim())
  if (filters?.name?.trim()) q.set('name', filters.name.trim())
  if (filters?.school_name?.trim()) q.set('school_name', filters.school_name.trim())
  const res = await apiFetch(`${getBaseUrl()}/api/admin/users?${q}`, {
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as AdminUserListResponse
}

export async function patchAdminUser(
  userId: string,
  payload: AdminUserUpdatePayload,
): Promise<AdminUser> {
  const res = await apiFetch(`${getBaseUrl()}/api/admin/users/${encodeURIComponent(userId)}`, {
    method: 'PATCH',
    headers: authHeadersJson(),
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as AdminUser
}

export async function fetchAdminBoards(
  page: number,
  pageSize: number,
  filters?: { board_id?: number; title?: string; user_id?: string },
): Promise<AdminBoardListResponse> {
  const q = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
  if (typeof filters?.board_id === 'number') q.set('board_id', String(filters.board_id))
  if (filters?.title?.trim()) q.set('title', filters.title.trim())
  if (filters?.user_id?.trim()) q.set('user_id', filters.user_id.trim())
  const res = await apiFetch(`${getBaseUrl()}/api/admin/boards?${q}`, {
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as AdminBoardListResponse
}

export async function patchAdminBoard(
  boardId: number,
  payload: AdminBoardUpdatePayload,
): Promise<AdminBoard> {
  const res = await apiFetch(`${getBaseUrl()}/api/admin/boards/${boardId}`, {
    method: 'PATCH',
    headers: authHeadersJson(),
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as AdminBoard
}

export async function deleteAdminBoard(boardId: number): Promise<void> {
  const res = await apiFetch(`${getBaseUrl()}/api/admin/boards/${boardId}`, {
    method: 'DELETE',
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
}

export async function fetchAdminReports(
  page: number,
  pageSize: number,
  filters?: { status?: string },
): Promise<AdminReportListResponse> {
  const q = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
  if (filters?.status) q.set('status', filters.status)
  const res = await apiFetch(`${getBaseUrl()}/api/admin/reports?${q}`, {
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as AdminReportListResponse
}

export async function patchAdminReport(
  reportId: number,
  payload: AdminReportUpdatePayload,
): Promise<AdminReport> {
  const res = await apiFetch(`${getBaseUrl()}/api/admin/reports/${reportId}`, {
    method: 'PATCH',
    headers: authHeadersJson(),
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as AdminReport
}
