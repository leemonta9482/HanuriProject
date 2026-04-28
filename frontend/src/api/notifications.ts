import type { UserNotificationListResponse } from './types'
import { apiFetch, authHeadersJson, getBaseUrl, parseJsonError } from './client'

/** 미확인 알림 목록 (기본 unread_only=true) */
export async function fetchMyNotifications(unreadOnly = true): Promise<UserNotificationListResponse> {
  const q = new URLSearchParams({ unread_only: unreadOnly ? 'true' : 'false' })
  const res = await apiFetch(`${getBaseUrl()}/api/auth/me/notifications?${q}`, { headers: authHeadersJson() })
  if (!res.ok) throw new Error(await parseJsonError(res))
  const data = (await res.json()) as UserNotificationListResponse
  return data
}

export async function markNotificationRead(notificationId: number): Promise<void> {
  const res = await apiFetch(`${getBaseUrl()}/api/auth/me/notifications/${notificationId}/read`, {
    method: 'PATCH',
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
}

export async function markChatRoomNotificationsRead(roomId: number): Promise<void> {
  const res = await apiFetch(`${getBaseUrl()}/api/auth/me/notifications/read-chat-room/${roomId}`, {
    method: 'PATCH',
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
}
