<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  closeChatRoom,
  deleteChatRoom,
  fetchChatMessages,
  fetchChatRooms,
  sendChatMessage,
} from '@/api/chat'
import { uploadsPublicUrl } from '@/api/client'
import type { ChatMessage, ChatRoomSummary } from '@/api/types'
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
let pollTimer: ReturnType<typeof setInterval> | null = null

const selectedRoom = computed(() => rooms.value.find((r) => r.room_id === selectedRoomId.value) ?? null)

function thumbUrl(path: string | null): string | null {
  if (!path) return null
  return uploadsPublicUrl(path)
}

function formatPrice(n: number | null): string {
  if (n == null || Number.isNaN(n)) return '가격 미정'
  return new Intl.NumberFormat('ko-KR').format(n) + '원'
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

function stopPoll() {
  if (pollTimer != null) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

async function loadMessages() {
  if (selectedRoomId.value == null) return
  loadingMessages.value = true
  try {
    messages.value = await fetchChatMessages(selectedRoomId.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '메시지를 불러오지 못했습니다.'
    messages.value = []
  } finally {
    loadingMessages.value = false
  }
}

async function pollNew() {
  if (selectedRoomId.value == null) return
  if (selectedRoom.value?.closed_at) return
  if (messages.value.length === 0) {
    await loadMessages()
    return
  }
  const last = messages.value[messages.value.length - 1]
  if (!last) return
  try {
    const more = await fetchChatMessages(selectedRoomId.value, last.message_id)
    if (more.length) messages.value = [...messages.value, ...more]
  } catch {
    /* ignore */
  }
}

function startPoll() {
  stopPoll()
  if (selectedRoom.value?.closed_at) return
  pollTimer = window.setInterval(() => void pollNew(), 4000)
}

async function selectRoom(id: number) {
  selectedRoomId.value = id
  void router.replace({ name: 'chat', query: { room: String(id) } })
  await loadMessages()
  stopPoll()
  const r = rooms.value.find((x) => x.room_id === id)
  if (r && !r.closed_at) startPoll()
}

async function onCloseChat() {
  const rid = selectedRoomId.value
  if (rid == null || selectedRoom.value?.closed_at) return
  if (!window.confirm('진짜 이 채팅방을 나가시겠습니까?')) return
  try {
    await closeChatRoom(rid)
    error.value = ''
    stopPoll()
    await loadRooms()
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
    stopPoll()
    selectedRoomId.value = null
    messages.value = []
    void router.replace({ name: 'chat', query: {} })
    await loadRooms()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '대화방을 삭제할 수 없습니다.'
  }
}

async function onSend() {
  const t = input.value.trim()
  if (!t || selectedRoomId.value == null || selectedRoom.value?.closed_at) return
  try {
    const m = await sendChatMessage(selectedRoomId.value, t)
    input.value = ''
    messages.value = [...messages.value, m]
    void loadRooms()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '전송 실패'
  }
}

onMounted(async () => {
  await loadRooms()
  const roomQ = route.query.room
  const rid = typeof roomQ === 'string' ? Number(roomQ) : NaN
  if (!Number.isNaN(rid) && rid > 0) {
    selectedRoomId.value = rid
    await loadMessages()
    const r = rooms.value.find((x) => x.room_id === rid)
    if (r && !r.closed_at) startPoll()
  }
})

watch(
  () => route.query.room,
  async (q) => {
    const rid = typeof q === 'string' ? Number(q) : NaN
    if (Number.isNaN(rid) || rid <= 0) {
      selectedRoomId.value = null
      messages.value = []
      stopPoll()
      return
    }
    if (selectedRoomId.value !== rid) {
      selectedRoomId.value = rid
      await loadMessages()
      stopPoll()
      const r = rooms.value.find((x) => x.room_id === rid)
      if (r && !r.closed_at) startPoll()
    }
  },
)

onUnmounted(() => stopPoll())
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
                <span v-else class="room-thumb-ph">{{ r.listing_kind === 'wanted' ? '희망' : '상품' }}</span>
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
            <div class="listing-bar">
              <div v-if="thumbUrl(selectedRoom.thumbnail_path)" class="lb-thumb">
                <img :src="thumbUrl(selectedRoom.thumbnail_path)!" alt="" />
              </div>
              <div class="lb-meta">
                <span class="lb-title">{{ selectedRoom.listing_title }}</span>
                <span class="lb-price">{{ formatPrice(selectedRoom.listing_price) }}</span>
              </div>
            </div>
          </div>

          <p v-if="selectedRoom.closed_at" class="closed-banner" role="status">
            종료된 대화입니다. 더 이상 메시지를 보낼 수 없습니다.
          </p>

          <div class="msg-scroll">
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
            </ul>
          </div>

          <form v-if="!selectedRoom.closed_at" class="composer" @submit.prevent="onSend">
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
  border: 1px solid var(--color-border);
  border-radius: 12px;
  overflow: hidden;
  background: var(--color-background-soft);
  min-height: 420px;
}

.sidebar {
  width: min(100%, 320px);
  flex-shrink: 0;
  border-right: 1px solid var(--color-border);
  background: var(--color-background);
  display: flex;
  flex-direction: column;
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
  overflow-y: auto;
  max-height: min(70vh, 560px);
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
  background: hsla(160, 100%, 37%, 0.1);
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
  font-size: 0.7rem;
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
  display: flex;
  flex-direction: column;
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
  margin: 0;
  padding: 0.65rem 1rem;
  font-size: 0.88rem;
  background: hsla(0, 60%, 50%, 0.08);
  color: #a33030;
  border-bottom: 1px solid var(--color-border);
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
  background: hsla(160, 100%, 37%, 0.15);
  color: hsl(160, 70%, 28%);
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
}

.lb-price {
  font-size: 0.85rem;
  color: var(--color-heading);
  font-weight: 700;
}

.msg-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 0.75rem 1rem;
  min-height: 200px;
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

.bubble {
  max-width: min(82%, 420px);
  padding: 0.55rem 0.75rem;
  border-radius: 12px;
  background: var(--color-background);
  border: 1px solid var(--color-border);
}

.msg-row.me .bubble {
  background: hsla(160, 100%, 37%, 0.12);
  border-color: hsla(160, 100%, 37%, 0.35);
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
  background: hsla(160, 100%, 37%, 1);
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
  }

  .sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--color-border);
    max-height: 40vh;
  }

  .room-list {
    max-height: 36vh;
  }
}
</style>
