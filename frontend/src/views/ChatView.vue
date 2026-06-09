<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import type { RouteLocationRaw } from 'vue-router'

import {
  blockUser,
  closeChatRoom,
  deleteChatRoom,
  fetchBlockedUsers,
  fetchChatMessages,
  fetchChatRooms,
  getWsChatUrl,
  unblockUser,
} from '@/api/chat'
import { uploadsPublicUrl } from '@/api/client'
import type { BlockedUserEntry, ChatMessage, ChatRoomClosed, ChatRoomSummary } from '@/api/types'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const rooms = ref<ChatRoomSummary[]>([])
const selectedRoomId = ref<number | null>(null)
const messages = ref<ChatMessage[]>([])
const input = ref('')
const loadingRooms = ref(true)
const loadingMessages = ref(false)
const error = ref('')
/** 실시간: 상대 종료 vs 내 종료 vs(새로고침 후) 공통 문구 */
const roomClosure = ref<ChatRoomClosed | null>(null)
const blockedUsers = ref<BlockedUserEntry[]>([])
const blockPanelOpen = ref(false)
const loadingBlocks = ref(false)

let chatWs: WebSocket | null = null
let wsReconnectTimer: ReturnType<typeof setTimeout> | null = null
let wsReconnectCount = 0
const WS_MAX_RECONNECT = 5
let wsIntentionalClose = false
let wsCurrentRoomId: number | null = null

const msgScrollRef = ref<HTMLElement | null>(null)

function scrollChatToBottom() {
  void nextTick(() => {
    requestAnimationFrame(() => {
      const el = msgScrollRef.value
      if (!el) return
      el.scrollTop = el.scrollHeight
    })
  })
}

const selectedRoom = computed(() => rooms.value.find((r) => r.room_id === selectedRoomId.value) ?? null)

function thumbUrl(path: string | null): string | null {
  if (!path) return null
  return uploadsPublicUrl(path)
}

function formatPrice(n: number | null): string {
  if (n == null || Number.isNaN(n)) return '가격 미정'
  return new Intl.NumberFormat('ko-KR').format(n) + '원'
}

function listingDetailTo(room: ChatRoomSummary): RouteLocationRaw {
  if (room.listing_kind === 'wanted') {
    return { name: 'wanted-detail', params: { id: String(room.listing_id) } }
  }
  return { name: 'board-detail', params: { id: String(room.listing_id) } }
}

function formatTime(iso: string | undefined | null): string {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    return d.toLocaleString('ko-KR', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}

function msgTime(iso: string | undefined | null): string {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    return d.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}

async function loadRooms() {
  loadingRooms.value = true
  error.value = ''
  try {
    rooms.value = await fetchChatRooms()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '목록을 불러오지 못했습니다.'
  } finally {
    loadingRooms.value = false
  }
}

async function loadBlockList() {
  loadingBlocks.value = true
  try {
    blockedUsers.value = await fetchBlockedUsers()
  } catch {
    blockedUsers.value = []
  } finally {
    loadingBlocks.value = false
  }
}

async function toggleBlockPanel() {
  blockPanelOpen.value = !blockPanelOpen.value
  if (blockPanelOpen.value) {
    await loadBlockList()
  }
}

async function onBlockPeer() {
  const room = selectedRoom.value
  if (!room?.i_am_peer || room.initiator_blocked_by_me || room.closed_at) return
  if (
    !window.confirm(
      '이 구매자를 차단하시겠습니까? 차단 후 상대는 새 대화를 걸거나 메시지를 보낼 수 없습니다.',
    )
  )
    return
  try {
    await blockUser(room.peer_user_id)
    error.value = ''
    await loadRooms()
    await loadBlockList()
    await loadMessages()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '차단에 실패했습니다.'
  }
}

async function onUnblockPeer(blockedUserId: string) {
  if (!window.confirm('이 사용자의 차단을 해제할까요?')) return
  try {
    await unblockUser(blockedUserId)
    error.value = ''
    await loadBlockList()
    await loadRooms()
    if (selectedRoomId.value != null) await loadMessages()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '해제에 실패했습니다.'
  }
}

function disconnectChatWs() {
  wsIntentionalClose = true
  if (wsReconnectTimer != null) {
    clearTimeout(wsReconnectTimer)
    wsReconnectTimer = null
  }
  if (chatWs != null) {
    chatWs.close()
    chatWs = null
  }
  wsReconnectCount = 0
  wsCurrentRoomId = null
}

function _openChatWs(roomId: number) {
  const token = localStorage.getItem('hanuri_token')
  if (!token) return
  const url = `${getWsChatUrl(roomId)}?token=${encodeURIComponent(token)}`
  const ws = new WebSocket(url)
  chatWs = ws

  ws.onmessage = (ev) => {
    try {
      const data = JSON.parse(String(ev.data)) as Record<string, unknown>
      if (data.type === 'connected') {
        wsReconnectCount = 0
        if (messages.value.length > 0) {
          const lastId = messages.value[messages.value.length - 1].message_id
          void fetchChatMessages(roomId, lastId).then(({ messages: more, room_closed }) => {
            if (more.length) messages.value = [...messages.value, ...more]
            if (room_closed) {
              roomClosure.value = room_closed
              disconnectChatWs()
              void loadRooms()
            }
          }).catch(() => {})
        }
      } else if (data.type === 'message') {
        const msg = data as unknown as ChatMessage
        if (!messages.value.some((m) => m.message_id === msg.message_id)) {
          messages.value = [...messages.value, msg]
        }
        void loadRooms()
      } else if (data.type === 'room_closed') {
        roomClosure.value = { notice_text: '상대방이 대화를 종료했습니다.' }
        disconnectChatWs()
        void loadRooms()
      } else if (data.type === 'error') {
        const detail = typeof data.detail === 'string' ? data.detail : ''
        if (detail === 'room_closed') {
          roomClosure.value = { notice_text: '종료된 채팅방입니다.' }
          disconnectChatWs()
        } else if (detail === 'blocked') {
          error.value = '차단된 대화방입니다. 메시지를 보낼 수 없습니다.'
        } else if (detail !== 'empty_message') {
          error.value = detail || '채팅 오류가 발생했습니다.'
        }
      }
    } catch {
      // ignore parse errors
    }
  }

  ws.onclose = () => {
    if (wsIntentionalClose || wsCurrentRoomId !== roomId) return
    if (wsReconnectCount >= WS_MAX_RECONNECT) {
      error.value = '연결이 끊겼습니다. 페이지를 새로고침해 주세요.'
      return
    }
    const delay = Math.min(1000 * Math.pow(2, wsReconnectCount), 30000)
    wsReconnectCount++
    wsReconnectTimer = setTimeout(() => {
      if (!wsIntentionalClose && wsCurrentRoomId === roomId) {
        _openChatWs(roomId)
      }
    }, delay)
  }

  ws.onerror = () => {
    // onclose handles reconnection
  }
}

function connectChatWs(roomId: number) {
  disconnectChatWs()
  wsIntentionalClose = false
  wsCurrentRoomId = roomId
  wsReconnectCount = 0
  _openChatWs(roomId)
}

async function loadMessages() {
  if (selectedRoomId.value == null) return
  loadingMessages.value = true
  try {
    const { messages: list, room_closed } = await fetchChatMessages(selectedRoomId.value)
    messages.value = list
    roomClosure.value = room_closed
    if (room_closed) disconnectChatWs()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '메시지를 불러오지 못했습니다.'
    messages.value = []
    roomClosure.value = null
  } finally {
    loadingMessages.value = false
  }
}

async function selectRoom(id: number) {
  selectedRoomId.value = id
  void router.replace({ name: 'chat', query: { room: String(id) } })
  await loadMessages()
  const r = rooms.value.find((x) => x.room_id === id)
  if (r && !r.closed_at) connectChatWs(id)
  else disconnectChatWs()
}

async function onCloseChat() {
  const rid = selectedRoomId.value
  if (rid == null || selectedRoom.value?.closed_at) return
  if (!window.confirm('진짜 이 채팅방을 나가시겠습니까?')) return
  try {
    const result = await closeChatRoom(rid)
    error.value = ''
    disconnectChatWs()
    if (result.deleted) {
      selectedRoomId.value = null
      messages.value = []
      roomClosure.value = null
      void router.replace({ name: 'chat', query: {} })
      await loadRooms()
      return
    }
    await loadRooms()
    await loadMessages()
    roomClosure.value = { notice_text: '내가 대화를 종료했습니다.' }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '대화를 종료할 수 없습니다.'
  }
}

async function onDeleteRoom() {
  const rid = selectedRoomId.value
  if (rid == null || !selectedRoom.value?.closed_at) return
  if (
    !window.confirm(
      '내 채팅 목록에서만 삭제합니다. 상대방 목록에는 그대로 보일 수 있습니다. 계속할까요?',
    )
  )
    return
  try {
    await deleteChatRoom(rid)
    error.value = ''
    disconnectChatWs()
    selectedRoomId.value = null
    messages.value = []
    roomClosure.value = null
    void router.replace({ name: 'chat', query: {} })
    await loadRooms()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '대화방을 삭제할 수 없습니다.'
  }
}

function onSend() {
  const t = input.value.trim()
  if (!t || selectedRoomId.value == null || selectedRoom.value?.closed_at) return
  if (selectedRoom.value?.i_am_blocked_by_peer) return
  if (selectedRoom.value?.i_am_peer && selectedRoom.value?.initiator_blocked_by_me) return
  if (!chatWs || chatWs.readyState !== WebSocket.OPEN) {
    error.value = '연결 중입니다. 잠시 후 다시 시도해 주세요.'
    return
  }
  chatWs.send(JSON.stringify({ type: 'message', body: t }))
  input.value = ''
}

function onHanuriLive(ev: Event) {
  const ce = ev as CustomEvent<Record<string, unknown>>
  const d = ce.detail
  if (!d) return
  if (d.type === 'chat_room_closed') {
    const rid = d.room_id
    if (typeof rid !== 'number') return
    const closedAt = typeof d.closed_at === 'string' ? d.closed_at : null
    rooms.value = rooms.value.map((r) =>
      r.room_id === rid ? { ...r, closed_at: closedAt ?? r.closed_at } : r,
    )
    if (selectedRoomId.value === rid) {
      roomClosure.value = { notice_text: '상대방이 대화를 종료했습니다.' }
      disconnectChatWs()
    }
    void loadRooms()
  } else if (d.type === 'chat') {
    // 현재 열려있지 않은 방(새 채팅방 포함)의 메시지 → 목록 갱신
    if (d.room_id !== selectedRoomId.value) {
      void loadRooms()
    }
  } else if (d.type === 'chat_blocked') {
    const roomIds = Array.isArray(d.room_ids) ? (d.room_ids as number[]) : []
    rooms.value = rooms.value.map((r) =>
      roomIds.includes(r.room_id) ? { ...r, i_am_blocked_by_peer: true } : r,
    )
    if (selectedRoomId.value != null && roomIds.includes(selectedRoomId.value)) {
      disconnectChatWs()
    }
  } else if (d.type === 'chat_unblocked') {
    const roomIds = Array.isArray(d.room_ids) ? (d.room_ids as number[]) : []
    void loadRooms().then(() => {
      if (selectedRoomId.value != null && roomIds.includes(selectedRoomId.value)) {
        const r = rooms.value.find((x) => x.room_id === selectedRoomId.value)
        if (r && !r.closed_at && !r.i_am_blocked_by_peer) {
          connectChatWs(selectedRoomId.value)
        }
      }
    })
  }
}

onMounted(async () => {
  window.addEventListener('hanuri:live', onHanuriLive)
  await loadRooms()
  const roomQ = route.query.room
  const rid = typeof roomQ === 'string' ? Number(roomQ) : NaN
  if (!Number.isNaN(rid) && rid > 0) {
    selectedRoomId.value = rid
    await loadMessages()
    const r = rooms.value.find((x) => x.room_id === rid)
    if (r && !r.closed_at) connectChatWs(rid)
  }
})

watch(
  () => route.query.room,
  async (q) => {
    const rid = typeof q === 'string' ? Number(q) : NaN
    if (Number.isNaN(rid) || rid <= 0) {
      selectedRoomId.value = null
      messages.value = []
      roomClosure.value = null
      disconnectChatWs()
      return
    }
    if (selectedRoomId.value !== rid) {
      selectedRoomId.value = rid
      await loadMessages()
      const r = rooms.value.find((x) => x.room_id === rid)
      if (r && !r.closed_at) connectChatWs(rid)
      else disconnectChatWs()
    }
  },
)

onUnmounted(() => {
  window.removeEventListener('hanuri:live', onHanuriLive)
  disconnectChatWs()
})

watch([messages, roomClosure], () => scrollChatToBottom(), { deep: true })

watch(loadingMessages, (loading) => {
  if (!loading) scrollChatToBottom()
})
</script>

<template>
  <div class="chat-page">
    <header class="page-head">
      <h1 class="title">채팅</h1>
      <p class="sub">구매하기로 시작한 대화 목록입니다. 왼쪽에서 상대를 고르면 오른쪽에서 메시지를 주고받을 수 있습니다.</p>
    </header>
    <p v-if="error" class="err" role="alert">{{ error }}</p>

    <div class="split">
      <aside class="sidebar" aria-label="대화 목록">
        <div class="block-panel">
          <button type="button" class="block-panel-toggle" @click="toggleBlockPanel">
            {{ blockPanelOpen ? '▼' : '▶' }} 차단 목록
            <span v-if="blockedUsers.length" class="block-count">({{ blockedUsers.length }})</span>
          </button>
          <div v-show="blockPanelOpen" class="block-panel-body">
            <p v-if="loadingBlocks" class="side-hint">불러오는 중…</p>
            <ul v-else-if="blockedUsers.length" class="block-list">
              <li v-for="b in blockedUsers" :key="b.blocked_user_id" class="block-row">
                <span class="block-name">{{ b.blocked_name }}</span>
                <button type="button" class="btn-unblock" @click="onUnblockPeer(b.blocked_user_id)">
                  해제
                </button>
              </li>
            </ul>
            <p v-else class="side-hint block-empty">차단한 구매자가 없습니다.</p>
          </div>
        </div>
        <p v-if="loadingRooms" class="side-hint">불러오는 중…</p>
        <ul v-else-if="rooms.length" class="room-list">
          <li v-for="r in rooms" :key="r.room_id">
            <button
              type="button"
              class="room-item"
              :class="{ active: selectedRoomId === r.room_id, ended: !!r.closed_at }"
              @click="selectRoom(r.room_id)"
            >
              <div class="room-thumb-wrap">
                <img v-if="thumbUrl(r.thumbnail_path)" :src="thumbUrl(r.thumbnail_path)!" alt="" />
                <span v-else class="room-thumb-ph">이미지 없음</span>
              </div>
              <div class="room-text">
                <span class="room-peer"
                  >{{ r.peer_name }}<span v-if="r.closed_at" class="ended-badge">종료</span></span
                >
                <span class="room-title">{{ r.listing_title }}</span>
                <span v-if="r.last_message_preview" class="room-preview">{{ r.last_message_preview }}</span>
                <span v-if="r.last_message_at" class="room-time">{{ formatTime(r.last_message_at) }}</span>
              </div>
            </button>
          </li>
        </ul>
        <p v-else class="side-empty">아직 대화가 없습니다. 판매글·구매 희망글에서 구매하기를 눌러 대화를 시작해 보세요.</p>
      </aside>

      <section class="main" aria-label="대화 내용">
        <div v-if="!selectedRoomId" class="empty-main">
          <div class="empty-icon" aria-hidden="true">💬</div>
          <p class="empty-msg">대화방을 선택해 주세요</p>
        </div>
        <template v-else-if="selectedRoom">
          <div class="chat-top">
            <div class="peer-line">
              <div class="peer-main">
                <strong>{{ selectedRoom.peer_name }}</strong>
                <span class="kind-badge">{{ selectedRoom.listing_kind === 'wanted' ? '구매 희망' : '판매' }}</span>
              </div>
              <div class="peer-actions">
                <button
                  v-if="
                    selectedRoom.i_am_peer &&
                    !selectedRoom.initiator_blocked_by_me &&
                    !selectedRoom.closed_at
                  "
                  type="button"
                  class="btn-block-peer"
                  @click="onBlockPeer"
                >
                  구매자 차단
                </button>
                <button
                  v-if="!selectedRoom.closed_at"
                  type="button"
                  class="btn-end-chat"
                  @click="onCloseChat"
                >
                  대화 끊기
                </button>
                <button
                  v-else
                  type="button"
                  class="btn-delete-room"
                  @click="onDeleteRoom"
                >
                  대화방 삭제
                </button>
              </div>
            </div>
            <div class="listing-bar">
              <div v-if="thumbUrl(selectedRoom.thumbnail_path)" class="lb-thumb">
                <img :src="thumbUrl(selectedRoom.thumbnail_path)!" alt="" />
              </div>
              <div class="lb-meta">
                <RouterLink class="lb-title lb-title-link" :to="listingDetailTo(selectedRoom)">
                  {{ selectedRoom.listing_title }}
                </RouterLink>
                <span class="lb-price">{{ formatPrice(selectedRoom.listing_price) }}</span>
              </div>
            </div>
          </div>

          <p v-if="selectedRoom.closed_at" class="closed-banner" role="status">
            종료된 대화입니다. 더 이상 메시지를 보낼 수 없습니다.
          </p>
          <p v-else-if="selectedRoom.i_am_blocked_by_peer" class="blocked-banner" role="status">
            판매자가 대화를 제한했습니다. 메시지를 보낼 수 없습니다.
          </p>
          <p
            v-else-if="selectedRoom.i_am_peer && selectedRoom.initiator_blocked_by_me"
            class="blocked-banner"
            role="status"
          >
            이 구매자를 차단한 대화입니다. 메시지를 보낼 수 없습니다.
          </p>

          <div ref="msgScrollRef" class="msg-scroll">
            <p v-if="loadingMessages" class="msg-hint">불러오는 중…</p>
            <ul v-else class="msg-list">
              <li
                v-for="m in messages"
                :key="m.message_id"
                class="msg-row"
                :class="{ me: m.sender_id === auth.user?.user_id }"
              >
                <div class="bubble">
                  <p class="msg-body">{{ m.body }}</p>
                  <time class="msg-time">{{ msgTime(m.created_at) }}</time>
                </div>
              </li>
              <li v-if="roomClosure" class="msg-row msg-system" role="status">
                <p class="msg-system-text">{{ roomClosure.notice_text }}</p>
              </li>
            </ul>
          </div>

          <form
            v-if="
              !selectedRoom.closed_at &&
              !selectedRoom.i_am_blocked_by_peer &&
              !(selectedRoom.i_am_peer && selectedRoom.initiator_blocked_by_me)
            "
            class="composer"
            @submit.prevent="onSend"
          >
            <input
              v-model="input"
              type="text"
              class="composer-input"
              maxlength="2000"
              placeholder="메시지를 입력하세요."
              autocomplete="off"
            />
            <button type="submit" class="composer-send" :disabled="!input.trim()">보내기</button>
          </form>
        </template>
      </section>
    </div>
  </div>
</template>

<style scoped>
.chat-page {
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 0.5rem 2rem;
  min-height: min(78vh, 720px);
  display: flex;
  flex-direction: column;
}

.page-head {
  margin-bottom: 1rem;
}

.title {
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--color-heading);
  margin-bottom: 0.35rem;
}

.sub {
  font-size: 0.9rem;
  color: var(--color-text);
  opacity: 0.9;
  margin: 0;
  line-height: 1.45;
}

.err {
  color: #c0392b;
  margin-bottom: 0.75rem;
}

.split {
  display: flex;
  flex: 1 1 auto;
  min-height: 0;
  width: 100%;
  height: clamp(420px, 65vh, 640px);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  overflow: hidden;
  background: var(--color-background-soft);
}

.sidebar {
  width: min(100%, 320px);
  flex-shrink: 0;
  min-height: 0;
  border-right: 1px solid var(--color-border);
  background: var(--color-background);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.side-hint,
.side-empty {
  padding: 1rem;
  font-size: 0.88rem;
  color: var(--color-text);
  opacity: 0.85;
  line-height: 1.45;
}

.room-list {
  list-style: none;
  margin: 0;
  padding: 0;
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.room-item {
  display: flex;
  gap: 0.65rem;
  width: 100%;
  text-align: left;
  padding: 0.65rem 0.75rem;
  border: none;
  border-bottom: 1px solid var(--color-border);
  background: transparent;
  cursor: pointer;
  color: inherit;
  font: inherit;
}

.room-item:hover {
  background: var(--color-background-mute);
}

.room-item.active {
  background: rgba(92, 176, 185, 0.1);
}

.room-thumb-wrap {
  width: 48px;
  height: 48px;
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
  background: var(--color-background-mute);
}

.room-thumb-wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.room-thumb-ph {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  padding: 0 0.15rem;
  box-sizing: border-box;
  text-align: center;
  line-height: 1.15;
  font-size: 0.58rem;
  color: var(--color-text);
  opacity: 0.7;
}

.room-text {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.room-peer {
  font-weight: 600;
  font-size: 0.92rem;
}

.room-title {
  font-size: 0.8rem;
  opacity: 0.85;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.room-preview {
  font-size: 0.78rem;
  opacity: 0.75;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.room-time {
  font-size: 0.72rem;
  opacity: 0.65;
}

.main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.empty-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: var(--color-text);
  opacity: 0.75;
}

.empty-icon {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.empty-msg {
  font-size: 1rem;
  margin: 0;
}

.chat-top {
  flex-shrink: 0;
  padding: 0.85rem 1rem;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-background);
}

.peer-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.65rem;
  flex-wrap: wrap;
}

.peer-main {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  min-width: 0;
}

.btn-end-chat {
  flex-shrink: 0;
  padding: 0.35rem 0.65rem;
  font-size: 0.82rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
  color: var(--color-text);
  cursor: pointer;
}

.btn-end-chat:hover {
  border-color: #c0392b;
  color: #c0392b;
}

.btn-delete-room {
  flex-shrink: 0;
  padding: 0.35rem 0.65rem;
  font-size: 0.82rem;
  border-radius: 8px;
  border: 1px solid #c0392b;
  background: transparent;
  color: #c0392b;
  cursor: pointer;
  font-weight: 600;
}

.btn-delete-room:hover {
  background: hsla(0, 55%, 45%, 0.1);
}

.closed-banner {
  flex-shrink: 0;
  margin: 0;
  padding: 0.65rem 1rem;
  font-size: 0.88rem;
  background: hsla(0, 60%, 50%, 0.08);
  color: #a33030;
  border-bottom: 1px solid var(--color-border);
}

.blocked-banner {
  flex-shrink: 0;
  margin: 0;
  padding: 0.65rem 1rem;
  font-size: 0.88rem;
  background: hsla(0, 60%, 50%, 0.08);
  color: #a33030;
  border-bottom: 1px solid var(--color-border);
}

.peer-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.45rem;
}

.btn-block-peer {
  flex-shrink: 0;
  padding: 0.35rem 0.65rem;
  font-size: 0.82rem;
  border-radius: 8px;
  border: 1px solid rgba(92, 176, 185, 0.55);
  background: rgba(92, 176, 185, 0.1);
  color: hsl(186, 38%, 26%);
  cursor: pointer;
  font-weight: 600;
}

.btn-block-peer:hover {
  background: rgba(92, 176, 185, 0.18);
}

.block-panel {
  flex-shrink: 0;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-background-mute);
}

.block-panel-toggle {
  width: 100%;
  text-align: left;
  padding: 0.6rem 0.75rem;
  border: none;
  background: transparent;
  font: inherit;
  font-size: 0.86rem;
  font-weight: 600;
  color: var(--color-text);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.block-panel-toggle:hover {
  background: rgba(92, 176, 185, 0.08);
}

.block-count {
  font-weight: 500;
  opacity: 0.8;
  font-size: 0.82rem;
}

.block-panel-body {
  padding: 0 0.65rem 0.65rem;
  max-height: 200px;
  overflow-y: auto;
}

.block-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.block-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.4rem 0.5rem;
  border-radius: 8px;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  font-size: 0.82rem;
}

.block-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btn-unblock {
  flex-shrink: 0;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background: transparent;
  cursor: pointer;
  color: hsl(186, 38%, 30%);
  font-weight: 600;
}

.btn-unblock:hover {
  background: rgba(92, 176, 185, 0.12);
}

.block-empty {
  margin: 0;
  padding: 0.25rem 0;
}

.ended-badge {
  margin-left: 0.35rem;
  font-size: 0.68rem;
  font-weight: 600;
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
  background: hsl(0, 0%, 78%);
  color: hsl(0, 0%, 28%);
}

.room-item.ended {
  opacity: 0.78;
}

.kind-badge {
  font-size: 0.72rem;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  background: rgba(92, 176, 185, 0.15);
  color: hsl(186, 38%, 28%);
  font-weight: 600;
}

.listing-bar {
  display: flex;
  gap: 0.65rem;
  align-items: center;
}

.lb-thumb {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--color-background-mute);
}

.lb-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.lb-meta {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.lb-title {
  font-size: 0.88rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

.lb-title-link {
  color: inherit;
  text-decoration: none;
  cursor: pointer;
  display: block;
}

.lb-title-link:hover {
  text-decoration: underline;
}

.lb-price {
  font-size: 0.85rem;
  color: var(--color-heading);
  font-weight: 700;
}

.msg-scroll {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
  padding: 0.75rem 1rem;
}

/* 스크롤바 — 브랜드 톤, 얇은 트랙 + 둥근 썸 */
.room-list,
.msg-scroll {
  scrollbar-width: thin;
  scrollbar-color: rgba(var(--color-accent-rgb), 0.52) rgba(0, 0, 0, 0.06);
}

.room-list::-webkit-scrollbar,
.msg-scroll::-webkit-scrollbar {
  width: 7px;
}

.room-list::-webkit-scrollbar-track,
.msg-scroll::-webkit-scrollbar-track {
  margin: 4px 0;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 100px;
}

.room-list::-webkit-scrollbar-thumb,
.msg-scroll::-webkit-scrollbar-thumb {
  background: linear-gradient(
    180deg,
    rgba(var(--color-accent-rgb), 0.55),
    rgba(var(--color-accent-rgb), 0.4)
  );
  border-radius: 100px;
  border: 2px solid transparent;
  background-clip: padding-box;
}

.room-list::-webkit-scrollbar-thumb:hover,
.msg-scroll::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(
    180deg,
    rgba(var(--color-accent-rgb), 0.72),
    rgba(var(--color-accent-rgb), 0.55)
  );
  background-clip: padding-box;
}

@media (prefers-color-scheme: dark) {
  .room-list,
  .msg-scroll {
    scrollbar-color: rgba(var(--color-accent-rgb), 0.58) rgba(255, 255, 255, 0.07);
  }

  .room-list::-webkit-scrollbar-track,
  .msg-scroll::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.06);
  }

  .room-list::-webkit-scrollbar-thumb,
  .msg-scroll::-webkit-scrollbar-thumb {
    background: linear-gradient(
      180deg,
      rgba(var(--color-accent-rgb), 0.6),
      rgba(var(--color-accent-rgb), 0.42)
    );
    background-clip: padding-box;
  }

  .room-list::-webkit-scrollbar-thumb:hover,
  .msg-scroll::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(
      180deg,
      rgba(var(--color-accent-rgb), 0.78),
      rgba(var(--color-accent-rgb), 0.58)
    );
    background-clip: padding-box;
  }
}

.msg-hint {
  text-align: center;
  font-size: 0.88rem;
  opacity: 0.8;
}

.msg-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.msg-row {
  display: flex;
  justify-content: flex-start;
}

.msg-row.me {
  justify-content: flex-end;
}

.msg-row.msg-system {
  justify-content: center;
  margin-top: 0.15rem;
}

.msg-system-text {
  margin: 0;
  padding: 0.35rem 0.75rem;
  font-size: 0.82rem;
  line-height: 1.45;
  color: var(--color-text);
  opacity: 0.85;
  text-align: center;
}

.bubble {
  max-width: min(82%, 420px);
  padding: 0.55rem 0.75rem;
  border-radius: 12px;
  background: var(--color-background);
  border: 1px solid var(--color-border);
}

.msg-row.me .bubble {
  background: rgba(92, 176, 185, 0.12);
  border-color: rgba(92, 176, 185, 0.35);
}

.msg-body {
  margin: 0;
  font-size: 0.92rem;
  line-height: 1.45;
  white-space: pre-wrap;
  word-break: break-word;
}

.msg-time {
  display: block;
  margin-top: 0.35rem;
  font-size: 0.72rem;
  opacity: 0.65;
}

.composer {
  flex-shrink: 0;
  display: flex;
  gap: 0.5rem;
  padding: 0.65rem 0.85rem;
  border-top: 1px solid var(--color-border);
  background: var(--color-background);
}

.composer-input {
  flex: 1;
  min-width: 0;
  padding: 0.55rem 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
  color: var(--color-text);
  font-size: 0.95rem;
}

.composer-send {
  flex-shrink: 0;
  padding: 0.55rem 1rem;
  border-radius: 8px;
  border: none;
  background: var(--color-accent);
  color: #fff;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
}

.composer-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .split {
    flex-direction: column;
    height: min(82vh, 760px);
    max-height: min(88vh, 800px);
    min-height: min(70vh, 640px);
  }

  .sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--color-border);
    max-height: 38vh;
    flex-shrink: 0;
  }

  .room-list {
    max-height: 34vh;
  }

  .main {
    flex: 1 1 auto;
    min-height: 0;
    overflow: hidden;
  }

  .msg-scroll {
    flex: 1 1 auto;
    min-height: 0;
  }
}
</style>
