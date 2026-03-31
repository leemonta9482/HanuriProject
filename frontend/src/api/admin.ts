import { authHeadersJson, getBaseUrl, parseJsonError } from './client'
import type {
  AdminBoardListResponse,
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
  const res = await fetch(`${getBaseUrl()}/api/admin/users?${q}`, {
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as AdminUserListResponse
}

export async function patchAdminUser(
  userId: string,
  payload: AdminUserUpdatePayload,
): Promise<AdminUser> {
  const res = await fetch(`${getBaseUrl()}/api/admin/users/${encodeURIComponent(userId)}`, {
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
  const res = await fetch(`${getBaseUrl()}/api/admin/boards?${q}`, {
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as AdminBoardListResponse
}
