<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'

import { getBaseUrl, notifySessionInvalid } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

interface LiveToastItem {
  id: number
  title: string
  body: string
  payload: Record<string, unknown>
}

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const searchQuery = ref('')

const sessionToast = ref({ show: false, message: '' })
/** 로그아웃 완료 등 — 화면 중앙 알림(브라우저 alert 대체) */
const centerAlert = ref({ show: false, message: '' })
const liveToasts = ref<LiveToastItem[]>([])
let sessionPollTimer: ReturnType<typeof setInterval> | null = null
let sessionInvalidOnce = false
let liveAbort: AbortController | null = null

/** 헤더 인사말: DB에 저장된 이름(실명)만 사용 */
const greetingName = computed(() => {
  const n = auth.user?.name?.trim()
  return n || ''
})

function onSessionInvalid(e: Event) {
  if (sessionInvalidOnce) return
  sessionInvalidOnce = true
  const ce = e as CustomEvent<{ message?: string }>
  const message =
    typeof ce.detail?.message === 'string' && ce.detail.message.trim()
      ? ce.detail.message.trim()
      : '다른 곳에서 로그인되어 로그아웃됩니다.'
  sessionToast.value = { show: true, message }
  void nextTick(() => {
    auth.logout()
    const name = route.name
    if (name !== 'login' && name !== 'register') {
      void router.push({ name: 'login' })
    }
    window.setTimeout(() => {
      sessionToast.value = { show: false, message: '' }
      sessionInvalidOnce = false
    }, 5200)
  })
}

onMounted(() => {
  if (auth.isLoggedIn) void auth.hydrateFromServer()
  window.addEventListener('hanuri:session-invalid', onSessionInvalid)
  /** 다른 기기에서 로그인한 뒤 이 탭이 API를 안 부르면 401을 못 받음 → 주기적으로 세션 확인 */
  sessionPollTimer = window.setInterval(() => {
    if (document.visibilityState !== 'visible' || !auth.isLoggedIn) return
    void auth.hydrateFromServer()
  }, 12_000)
})

onUnmounted(() => {
  stopLiveStream()
  window.removeEventListener('hanuri:session-invalid', onSessionInvalid)
  if (sessionPollTimer != null) {
    clearInterval(sessionPollTimer)
    sessionPollTimer = null
  }
})

watch(
  () => [route.name, route.query.q] as const,
  () => {
    if (route.name === 'home') {
      const raw = route.query.q
      const q = Array.isArray(raw) ? raw[0] : raw
      searchQuery.value = typeof q === 'string' ? q : ''
    } else {
      searchQuery.value = ''
    }
  },
  { immediate: true },
)

function onSearchSubmit() {
  const q = searchQuery.value.trim()
  void router.push({ name: 'home', query: q ? { q } : {} })
}

function clearNavSearch() {
  searchQuery.value = ''
  void router.push({ name: 'home', query: {} })
}

const canClearSearch = computed(() => {
  const raw = route.query.q
  const q = Array.isArray(raw) ? raw[0] : raw
  if (typeof q === 'string' && q.trim()) return true
  return searchQuery.value.trim().length > 0
})

async function onLogout() {
  auth.logout()
  centerAlert.value = { show: true, message: '로그아웃 되었습니다.' }
  await router.push({ name: 'home' })
}

function closeCenterAlert() {
  centerAlert.value = { show: false, message: '' }
}

function stopLiveStream() {
  liveAbort?.abort()
  liveAbort = null
}

function parseSseChunks(buffer: string): { events: Record<string, unknown>[]; rest: string } {
  const events: Record<string, unknown>[] = []
  const parts = buffer.split('\n\n')
  const rest = parts.pop() ?? ''
  for (const block of parts) {
    for (const line of block.split('\n')) {
      if (line.startsWith('data: ')) {
        try {
          events.push(JSON.parse(line.slice(6)) as Record<string, unknown>)
        } catch {
          /* ignore */
        }
        break
      }
    }
  }
  return { events, rest }
}

function pushLiveToast(ev: Record<string, unknown>) {
  const t = ev.type
  if (t !== 'chat' && t !== 'favorite') return
  const title = typeof ev.title === 'string' ? ev.title : '알림'
  const body = typeof ev.body === 'string' ? ev.body : ''
  const id = Date.now() + Math.random()
  liveToasts.value = [...liveToasts.value, { id, title, body, payload: ev }]
  window.setTimeout(() => {
    liveToasts.value = liveToasts.value.filter((x) => x.id !== id)
  }, 4500)
}

function onLiveToastClick(t: LiveToastItem) {
  const p = t.payload
  if (p.type === 'chat' && typeof p.room_id === 'number') {
    void router.push({ name: 'chat', query: { room: String(p.room_id) } })
  } else if (p.type === 'favorite' && typeof p.board_id === 'number') {
    void router.push({ name: 'board-detail', params: { id: String(p.board_id) } })
  }
}

async function readSseStream(body: ReadableStream<Uint8Array>, signal: AbortSignal) {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buf = ''
  while (!signal.aborted) {
    const { done, value } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })
    const { events, rest } = parseSseChunks(buf)
    buf = rest
    for (const ev of events) {
      const typ = ev.type
      if (typ === 'ping' || typ === 'connected') continue
      pushLiveToast(ev)
    }
  }
}

async function runLiveStream() {
  while (auth.isLoggedIn) {
    const token = localStorage.getItem('hanuri_token')
    if (!token) break
    const ac = new AbortController()
    liveAbort = ac
    try {
      const res = await fetch(`${getBaseUrl()}/api/events/stream`, {
        headers: { Authorization: `Bearer ${token}` },
        signal: ac.signal,
      })
      if (res.status === 401) {
        notifySessionInvalid()
        break
      }
      if (!res.ok || !res.body) {
        await new Promise((r) => setTimeout(r, 3000))
        continue
      }
      await readSseStream(res.body, ac.signal)
    } catch {
      /* 네트워크 끊김·abort */
    } finally {
      if (liveAbort === ac) liveAbort = null
    }
    if (!auth.isLoggedIn) break
    await new Promise((r) => setTimeout(r, 3000))
  }
}

watch(
  () => auth.isLoggedIn,
  (loggedIn) => {
    stopLiveStream()
    if (!loggedIn) liveToasts.value = []
    if (loggedIn) void runLiveStream()
  },
  { immediate: true },
)
</script>

<template>
  <div class="layout">
    <header class="header">
      <RouterLink to="/" class="brand">Hanuri</RouterLink>
      <form
        v-if="auth.isLoggedIn"
        class="header-search"
        role="search"
        aria-label="거래 글 검색"
        @submit.prevent="onSearchSubmit"
      >
        <input
          v-model="searchQuery"
          class="header-search-input"
          type="search"
          name="q"
          maxlength="100"
          placeholder="제목·설명·장소 검색"
          autocomplete="off"
        />
        <button type="submit" class="header-search-btn">검색</button>
        <button
          type="button"
          class="header-search-clear"
          :class="{ 'header-search-clear--hidden': !canClearSearch }"
          :tabindex="canClearSearch ? 0 : -1"
          :aria-hidden="!canClearSearch"
          @click="canClearSearch ? clearNavSearch() : undefined"
        >
          초기화
        </button>
      </form>
      <nav class="nav">
        <RouterLink to="/">거래</RouterLink>
        <template v-if="auth.isLoggedIn">
          <RouterLink to="/my-shop">내 상점</RouterLink>
          <RouterLink to="/chat">채팅</RouterLink>
          <RouterLink v-if="auth.isAdmin" to="/admin/users" class="admin-link">관리자 페이지</RouterLink>
          <span class="user"
            >{{ greetingName || '회원' }}님<span v-if="auth.isAdmin" class="badge">관리자</span></span
          >
          <button type="button" class="ghost" @click="onLogout">로그아웃</button>
        </template>
        <template v-else>
          <RouterLink to="/login">로그인</RouterLink>
          <RouterLink to="/register">회원가입</RouterLink>
        </template>
      </nav>
    </header>
    <main class="main">
      <RouterView />
    </main>
    <Teleport to="body">
      <div v-if="centerAlert.show" class="center-alert-backdrop" @click.self="closeCenterAlert">
        <div
          class="center-alert"
          role="alertdialog"
          aria-modal="true"
          aria-labelledby="center-alert-msg"
        >
          <p id="center-alert-msg" class="center-alert-text">{{ centerAlert.message }}</p>
          <button type="button" class="center-alert-btn" @click="closeCenterAlert">확인</button>
        </div>
      </div>
    </Teleport>
    <Teleport to="body">
      <div v-if="sessionToast.show" class="session-toast" role="alert">
        {{ sessionToast.message }}
      </div>
    </Teleport>
    <Teleport to="body">
      <div class="live-toast-stack" aria-live="polite">
        <button
          v-for="t in liveToasts"
          :key="t.id"
          type="button"
          class="live-toast"
          @click="onLiveToastClick(t)"
        >
          <span class="live-toast-title">{{ t.title }}</span>
          <span class="live-toast-body">{{ t.body }}</span>
        </button>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem 1rem;
  padding-bottom: 2rem;
  margin-bottom: 2.5rem;
  border-bottom: 1px solid var(--color-border);
}

.brand {
  font-weight: 700;
  font-size: 1.25rem;
  color: var(--color-heading);
  flex-shrink: 0;
}

.header-search {
  flex: 1 1 18rem;
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 0.5rem;
  min-width: min(100%, 16rem);
  max-width: 40rem;
}

/* 입력·버튼 동일 높이·패딩 */
.header-search-input,
.header-search-btn,
.header-search-clear {
  box-sizing: border-box;
  height: 2.5rem;
  min-height: 2.5rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.9rem;
  line-height: 1.35;
  border-radius: 8px;
}

.header-search-input {
  flex: 1 1 auto;
  min-width: 10rem;
  width: 0;
  -webkit-appearance: none;
  appearance: none;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
}

.header-search-input:focus {
  outline: none;
  border-color: hsla(160, 100%, 37%, 0.55);
  box-shadow: 0 0 0 2px hsla(160, 100%, 37%, 0.12);
}

.header-search-btn,
.header-search-clear {
  flex: 0 0 auto;
  min-width: 3.5rem;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
  color: var(--color-text);
  font-weight: 500;
  cursor: pointer;
}

.header-search-clear--hidden {
  visibility: hidden;
  pointer-events: none;
}

.header-search .header-search-btn {
  background: hsla(160, 100%, 37%, 1);
  border-color: transparent;
  color: #fff;
}

.header-search-btn:hover {
  filter: brightness(1.05);
}

.header-search-clear:hover {
  border-color: var(--color-border-hover);
}

.nav {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem 1rem;
  font-size: 0.95rem;
  width: 100%;
  justify-content: flex-end;
}

@media (min-width: 900px) {
  .header {
    flex-wrap: nowrap;
  }

  .nav {
    width: auto;
    justify-content: flex-end;
  }
}

.nav a.router-link-exact-active {
  color: var(--color-heading);
  font-weight: 600;
}

.admin-link {
  font-weight: 600;
  font-size: 0.95rem;
}

.user {
  font-size: 0.9rem;
  color: var(--color-text);
}

.badge {
  margin-left: 0.35rem;
  padding: 0.1rem 0.4rem;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 4px;
  background: hsla(160, 100%, 37%, 0.2);
  color: hsla(160, 100%, 28%, 1);
  vertical-align: middle;
}

.ghost {
  padding: 0.35rem 0.65rem;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-text);
  font-size: 0.9rem;
  cursor: pointer;
}

.ghost:hover {
  border-color: var(--color-border-hover);
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.center-alert-backdrop {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.45);
  animation: center-alert-fade 0.2s ease-out;
}

.center-alert {
  width: 100%;
  max-width: 22rem;
  padding: 1.35rem 1.25rem 1.15rem;
  border-radius: 12px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.22);
  text-align: center;
}

.center-alert-text {
  margin: 0 0 1.1rem;
  font-size: 0.98rem;
  line-height: 1.55;
}

.center-alert-btn {
  min-width: 6.5rem;
  padding: 0.55rem 1.1rem;
  border-radius: 8px;
  border: none;
  background: hsla(160, 100%, 37%, 1);
  color: #fff;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
}

.center-alert-btn:hover {
  filter: brightness(1.05);
}

@keyframes center-alert-fade {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.session-toast {
  position: fixed;
  left: 50%;
  bottom: 1.5rem;
  transform: translateX(-50%);
  z-index: 9999;
  max-width: min(92vw, 22rem);
  padding: 0.85rem 1.1rem;
  border-radius: 10px;
  background: hsl(0, 0%, 12%);
  color: #fff;
  font-size: 0.92rem;
  line-height: 1.45;
  text-align: center;
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.28);
  pointer-events: none;
  animation: session-toast-in 0.2s ease-out;
}

@keyframes session-toast-in {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

.live-toast-stack {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 9997;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.5rem;
  max-width: min(92vw, 22rem);
  pointer-events: none;
}

.live-toast {
  pointer-events: auto;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.25rem;
  text-align: left;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
  color: var(--color-text);
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.12);
  cursor: pointer;
  font: inherit;
  animation: live-toast-in 0.22s ease-out;
}

.live-toast:hover {
  border-color: var(--color-border-hover);
}

.live-toast-title {
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--color-heading);
}

.live-toast-body {
  font-size: 0.86rem;
  line-height: 1.4;
  opacity: 0.95;
}

@keyframes live-toast-in {
  from {
    opacity: 0;
    transform: translateX(12px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
</style>
