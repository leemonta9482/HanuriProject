import { computed, onUnmounted, ref, watch, type Ref } from 'vue'

import type { LoginUserInfo } from '@/api/types'
import {
  fetchMyNotifications,
  markChatRoomNotificationsRead,
  markNotificationRead,
} from '@/api/notifications'

export type InboxChat = {
  kind: 'chat'
  notification_id: number
  room_id: number
  title: string
  body: string
  at: number
}

export type InboxFavorite = {
  kind: 'favorite'
  notification_id: number
  board_id: number
  title: string
  body: string
  at: number
}

export type InboxItem = InboxChat | InboxFavorite

function parseAt(iso: string | null | undefined): number {
  if (!iso) return Date.now()
  const t = new Date(iso).getTime()
  return Number.isFinite(t) ? t : Date.now()
}

export function useNotificationInbox(userRef: Ref<LoginUserInfo | null>) {
  const items = ref<InboxItem[]>([])

  async function refreshFromServer(): Promise<void> {
    const uid = userRef.value?.user_id?.trim()
    if (!uid) {
      items.value = []
      return
    }
    try {
      const { items: rows } = await fetchMyNotifications(true)
      const mapped: InboxItem[] = []
      for (const n of rows) {
        if (n.kind === 'CHAT_MESSAGE' && n.room_id != null) {
          mapped.push({
            kind: 'chat',
            notification_id: n.notification_id,
            room_id: n.room_id,
            title: n.title?.trim() || '새 채팅',
            body: n.body ?? '',
            at: parseAt(n.created_at),
          })
        } else if (n.kind === 'BOARD_FAVORITED' && n.board_id != null) {
          mapped.push({
            kind: 'favorite',
            notification_id: n.notification_id,
            board_id: n.board_id,
            title: n.title?.trim() || '찜 알림',
            body: n.body ?? '',
            at: parseAt(n.created_at),
          })
        }
      }
      mapped.sort((a, b) => b.at - a.at)
      items.value = mapped
    } catch {
      /* 이전 목록 유지 */
    }
  }

  let debounceTimer: ReturnType<typeof setTimeout> | null = null
  function scheduleRefresh(): void {
    if (!userRef.value?.user_id?.trim()) return
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
      debounceTimer = null
      void refreshFromServer()
    }, 400)
  }

  let pollTimer: ReturnType<typeof setInterval> | null = null

  watch(
    () => userRef.value?.user_id,
    (uid) => {
      if (debounceTimer) {
        clearTimeout(debounceTimer)
        debounceTimer = null
      }
      if (pollTimer) {
        clearInterval(pollTimer)
        pollTimer = null
      }
      if (!uid?.trim()) {
        items.value = []
        return
      }
      void refreshFromServer()
      pollTimer = setInterval(() => void refreshFromServer(), 45_000)
    },
    { immediate: true },
  )

  onUnmounted(() => {
    if (debounceTimer) clearTimeout(debounceTimer)
    if (pollTimer) clearInterval(pollTimer)
  })

  /** WebSocket 수신 시 서버 목록 재조회(디바운스) */
  function ingestLive(_data: Record<string, unknown>): void {
    scheduleRefresh()
  }

  async function acknowledgeChat(roomId: number): Promise<void> {
    if (!userRef.value?.user_id) return
    try {
      await markChatRoomNotificationsRead(roomId)
      await refreshFromServer()
    } catch {
      items.value = items.value.filter((i) => !(i.kind === 'chat' && i.room_id === roomId))
    }
  }

  async function dismissFavorite(notificationId: number): Promise<void> {
    if (!userRef.value?.user_id) return
    try {
      await markNotificationRead(notificationId)
      await refreshFromServer()
    } catch {
      items.value = items.value.filter(
        (i) => !(i.kind === 'favorite' && i.notification_id === notificationId),
      )
    }
  }

  const count = computed(() => items.value.length)

  const sortedItems = computed(() => [...items.value].sort((a, b) => b.at - a.at))

  return {
    items: sortedItems,
    count,
    ingestLive,
    acknowledgeChat,
    dismissFavorite,
    sync: refreshFromServer,
    refreshNotifications: refreshFromServer,
  }
}
