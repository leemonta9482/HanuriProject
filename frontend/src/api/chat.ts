import type { BlockedUserEntry, ChatMessage, ChatRoomClosed, ChatRoomSummary } from './types'
import { apiFetch, authHeadersJson, getBaseUrl, parseJsonError } from './client'

export async function openChatRoom(payload: {
  kind: 'board' | 'wanted'
  board_id?: number
  wanted_id?: number
}): Promise<{ room_id: number }> {
  const res = await apiFetch(`${getBaseUrl()}/api/chat/rooms/open`, {
    method: 'POST',
    headers: authHeadersJson(),
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as { room_id: number }
}

export async function fetchChatRooms(): Promise<ChatRoomSummary[]> {
  const res = await apiFetch(`${getBaseUrl()}/api/chat/rooms`, {
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as ChatRoomSummary[]
}

export async function fetchChatMessages(
  roomId: number,
  afterId?: number,
): Promise<{ messages: ChatMessage[]; room_closed: ChatRoomClosed | null }> {
  const sp = new URLSearchParams()
  if (afterId != null) sp.set('after_id', String(afterId))
  const q = sp.toString()
  const res = await apiFetch(`${getBaseUrl()}/api/chat/rooms/${roomId}/messages${q ? `?${q}` : ''}`, {
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  const data = (await res.json()) as { messages: ChatMessage[]; room_closed: ChatRoomClosed | null }
  return { messages: data.messages, room_closed: data.room_closed ?? null }
}

export async function sendChatMessage(roomId: number, body: string): Promise<ChatMessage> {
  const res = await apiFetch(`${getBaseUrl()}/api/chat/rooms/${roomId}/messages`, {
    method: 'POST',
    headers: authHeadersJson(),
    body: JSON.stringify({ body }),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as ChatMessage
}

/** deleted: 메시지 없이 구매자만 끊은 경우 방이 DB에서 삭제됨 */
export async function closeChatRoom(roomId: number): Promise<{ deleted?: boolean }> {
  const res = await apiFetch(`${getBaseUrl()}/api/chat/rooms/${roomId}/close`, {
    method: 'POST',
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as { deleted?: boolean }
}

/** 종료된 방만, 내 목록에서만 숨김(상대 목록은 유지). 둘 다 삭제 시 서버에서 방 삭제 */
export async function deleteChatRoom(roomId: number): Promise<void> {
  const res = await apiFetch(`${getBaseUrl()}/api/chat/rooms/${roomId}`, {
    method: 'DELETE',
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
}

export async function fetchBlockedUsers(): Promise<BlockedUserEntry[]> {
  const res = await apiFetch(`${getBaseUrl()}/api/chat/blocks`, {
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as BlockedUserEntry[]
}

export async function blockUser(blockedUserId: string): Promise<BlockedUserEntry> {
  const res = await apiFetch(`${getBaseUrl()}/api/chat/blocks`, {
    method: 'POST',
    headers: authHeadersJson(),
    body: JSON.stringify({ blocked_user_id: blockedUserId }),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
  return (await res.json()) as BlockedUserEntry
}

export async function unblockUser(blockedUserId: string): Promise<void> {
  const res = await apiFetch(`${getBaseUrl()}/api/chat/blocks/${encodeURIComponent(blockedUserId)}`, {
    method: 'DELETE',
    headers: authHeadersJson(),
  })
  if (!res.ok) throw new Error(await parseJsonError(res))
}
