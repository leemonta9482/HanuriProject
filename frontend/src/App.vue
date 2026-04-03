<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'

import { getBaseUrl, notifySessionInvalid, uploadsPublicUrl } from '@/api/client'
import hanuriMark from '@/assets/hanuri-mark.png'
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

function routeQueryIsWanted(): boolean {
  const t = route.query.type
  return t === 'wanted' || (Array.isArray(t) && t.includes('wanted'))
}

/** 글 작성: 판매(board) 탭이 현재 경로와 일치 */
const isActivePostWriteBoard = computed(
  () => route.name === 'post-write' && !routeQueryIsWanted(),
)
/** 글 작성: 구매 희망(wanted) 탭이 현재 경로와 일치 */
const isActivePostWriteWanted = computed(
  () => route.name === 'post-write' && routeQueryIsWanted(),
)

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

const BRAND_PHRASES = ['대학생 중고 거래는?', '하누리에서!'] as const
const BRAND_MS_TYPE = 120
const BRAND_MS_DELETE = 70
/** 다 쓴 뒤 → 지우기 전 대기 */
const BRAND_HOLD_FULL = 1000
/** 다 지운 뒤 → 다음 문구 타이핑 전 대기 */
const BRAND_WAIT_AFTER_ERASE = 500

const brandTypedText = ref('')
let brandTypingCancelled = false

function stopBrandTyping() {
  brandTypingCancelled = true
}

function brandSleep(ms: number) {
  return new Promise<void>((resolve) => {
    window.setTimeout(resolve, ms)
  })
}

async function runBrandTypingLoop() {
  brandTypingCancelled = false
  let idx = 0
  while (!brandTypingCancelled) {
    const phrase = BRAND_PHRASES[idx % BRAND_PHRASES.length] ?? BRAND_PHRASES[0]
    for (let i = 0; i < phrase.length; i++) {
      if (brandTypingCancelled) return
      brandTypedText.value += phrase.charAt(i)
      await brandSleep(BRAND_MS_TYPE)
    }
    if (brandTypingCancelled) return
    await brandSleep(BRAND_HOLD_FULL)
    while (brandTypedText.value.length > 0) {
      if (brandTypingCancelled) return
      brandTypedText.value = brandTypedText.value.slice(0, -1)
      await brandSleep(BRAND_MS_DELETE)
    }
    if (brandTypingCancelled) return
    await brandSleep(BRAND_WAIT_AFTER_ERASE)
    idx += 1
  }
}

function startBrandTyping() {
  if (typeof window === 'undefined') return
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    brandTypedText.value = BRAND_PHRASES[0]
    return
  }
  void runBrandTypingLoop()
}

onMounted(() => {
  if (auth.isLoggedIn) void auth.hydrateFromServer()
  window.addEventListener('hanuri:session-invalid', onSessionInvalid)
  /** 다른 기기에서 로그인한 뒤 이 탭이 API를 안 부르면 401을 못 받음 → 주기적으로 세션 확인 */
  sessionPollTimer = window.setInterval(() => {
    if (document.visibilityState !== 'visible' || !auth.isLoggedIn) return
    void auth.hydrateFromServer()
  }, 12_000)
  startBrandTyping()
})

onUnmounted(() => {
  stopBrandTyping()

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
    <header
      class="header"
      :class="[auth.isLoggedIn ? 'header--with-search' : 'header--no-search']"
    >
      <div class="header-brand">
        <RouterLink to="/" class="brand" aria-label="우리 대학 하누리, 홈으로 이동">
          <img class="brand-logo" :src="hanuriMark" alt="" width="34" height="34" />
          <span class="brand-typed-line" aria-hidden="true">
            <span class="brand-typed-inner">
              <span class="brand-typed">{{ brandTypedText }}</span><span class="brand-cursor" aria-hidden="true"></span>
            </span>
          </span>
        </RouterLink>
      </div>
      <form
        v-if="auth.isLoggedIn"
        class="header-search"
        role="search"
        aria-label="거래 글 검색"
        @submit.prevent="onSearchSubmit"
      >
        <div class="header-search-box">
          <input
            v-model="searchQuery"
            class="header-search-input"
            type="search"
            name="q"
            maxlength="100"
            placeholder="상품명, 지역명, @상점명 입력"
            autocomplete="off"
          />
          <button type="submit" class="header-search-submit" aria-label="검색">
            <svg class="header-search-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
              <path
                fill="currentColor"
                d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"
              />
            </svg>
          </button>
        </div>
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
        <template v-if="auth.isLoggedIn">
          <div class="nav-cluster">
            <div class="nav-write-dropdown">
              <button
                type="button"
                class="nav-write-dropdown-trigger"
                aria-haspopup="menu"
                aria-label="새 글 작성 — 호버하여 판매하기 또는 구매하기 선택"
              >
                <span class="nav-write-dropdown-plus" aria-hidden="true">
                  <svg
                    class="nav-write-dropdown-icon"
                    viewBox="0 0 24 24"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M12 5v14M5 12h14"
                      stroke="currentColor"
                      stroke-width="2.25"
                      stroke-linecap="round"
                    />
                  </svg>
                </span>
              </button>
              <div class="nav-write-dropdown-menu" role="menu" aria-label="글 종류">
                <RouterLink
                  :to="{ name: 'post-write' }"
                  class="nav-user-dropdown-item"
                  active-class=""
                  exact-active-class=""
                  :class="{ 'nav-write-menu-item--here': isActivePostWriteBoard }"
                  role="menuitem"
                >
                  판매하기
                </RouterLink>
                <RouterLink
                  :to="{ name: 'post-write', query: { type: 'wanted' } }"
                  class="nav-user-dropdown-item"
                  active-class=""
                  exact-active-class=""
                  :class="{ 'nav-write-menu-item--here': isActivePostWriteWanted }"
                  role="menuitem"
                >
                  구매하기
                </RouterLink>
              </div>
            </div>
            <div class="nav-user-dropdown">
              <div class="nav-user-dropdown-trigger" tabindex="0">
                <RouterLink
                  to="/profile"
                  class="nav-user-dropdown-profile-link"
                  aria-label="프로필로 이동"
                >
                  <span class="nav-user-dropdown-avatar">
                    <img
                      v-if="auth.user?.profile_image_path?.trim()"
                      :src="uploadsPublicUrl(auth.user.profile_image_path.trim())"
                      alt=""
                      class="nav-avatar"
                      width="28"
                      height="28"
                    />
                    <span v-else class="nav-avatar nav-avatar--ph" aria-hidden="true">{{
                      (greetingName || '?').slice(0, 1)
                    }}</span>
                  </span>
                  <span class="user-text">
                    <span class="user-name">{{ greetingName || '회원' }}님</span>
                    <span v-if="auth.isAdmin" class="badge">관리자</span>
                  </span>
                </RouterLink>
                <span class="nav-user-dropdown-caret" aria-hidden="true">▾</span>
              </div>
              <div class="nav-user-dropdown-menu" role="menu" aria-label="빠른 이동">
                <div v-if="auth.isAdmin" class="nav-admin-dropdown-block" role="group" aria-label="관리자 페이지">
                  <RouterLink
                    :to="{ name: 'admin-users' }"
                    class="nav-user-dropdown-item"
                    role="menuitem"
                  >
                    회원 관리
                  </RouterLink>
                  <RouterLink
                    :to="{ name: 'admin-boards' }"
                    class="nav-user-dropdown-item"
                    role="menuitem"
                  >
                    게시글 관리
                  </RouterLink>
                  <RouterLink
                    :to="{ name: 'admin-reports' }"
                    class="nav-user-dropdown-item"
                    role="menuitem"
                  >
                    신고 관리
                  </RouterLink>
                </div>
                <RouterLink to="/chat" class="nav-user-dropdown-item" role="menuitem">채팅</RouterLink>
                <RouterLink to="/my-shop" class="nav-user-dropdown-item" role="menuitem">내 상점</RouterLink>
                <RouterLink
                  :to="{ name: 'favorites' }"
                  class="nav-user-dropdown-item"
                  role="menuitem"
                  aria-label="찜한 상품 목록"
                >
                  찜 목록
                </RouterLink>
                <button
                  type="button"
                  class="nav-user-dropdown-item nav-user-dropdown-item--logout"
                  role="menuitem"
                  @click="onLogout"
                >
                  로그아웃
                </button>
              </div>
            </div>
          </div>
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
  display: grid;
  align-items: center;
  gap: 0.75rem 1rem;
  padding-bottom: 2rem;
  margin-bottom: 2.5rem;
  border-bottom: 1px solid var(--color-border);
}

/* 로그인: 브랜드 | 검색 | 네비 — 좌·우 1fr 대칭으로 검색 입력이 뷰포트 정중앙에 맞음.
 * 검색 열: min(40rem, 100vw - 38.125rem) 단일 규칙 — 1250·1251px에서도 같은 값(40rem)이 나와 미디어쿼리 전환 시 툭 줄어듦이 없음. */
.header--with-search {
  grid-template-columns:
    minmax(0, 1fr)
    minmax(0, min(40rem, max(0px, calc(100vw - 38.125rem))))
    minmax(0, 1fr);
  column-gap: clamp(0.75rem, 2vw, 1.25rem);
}

/* 왼쪽 1fr 트랙 안에서 로고 블록을 트랙의 가로 중앙에 (붙어 보이지 않도록 shrink-wrap + center) */
.header--with-search .header-brand {
  justify-self: center;
  width: max-content;
  max-width: 100%;
  box-sizing: border-box;
  justify-content: center;
}

.header--with-search .nav {
  justify-self: end;
}

/* 비로그인: 좌·우 1fr로 대칭 → 가운데 열(auto)의 로고가 뷰포트 정중앙에 맞음 */
.header--no-search {
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  column-gap: 1rem;
}

.header--no-search .header-brand {
  grid-column: 2;
  justify-self: center;
}

.header--no-search .nav {
  grid-column: 3;
  justify-self: stretch;
  justify-content: flex-end;
}

/* 로고+글자: 해당 열 안에서 가로·세로 중앙 */
.header-brand {
  min-width: 0;
  display: flex;
  justify-content: center;
  align-items: center;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: clamp(1rem, 0.95rem + 0.2vw, 1.125rem);
  color: var(--color-heading);
  flex-shrink: 0;
  text-decoration: none;
  /* 로고(고정) + 글 상자(고정 폭) → 타이핑 중에도 전체 폭이 거의 일정 */
  min-width: 0;
}

/* 로고: em 아닌 고정 rem — 글 애니메이션과 무관하게 크기·위치 유지 */
.brand-logo {
  flex: 0 0 2.125rem;
  width: 2.125rem;
  height: 2.125rem;
  min-width: 2.125rem;
  min-height: 2.125rem;
  object-fit: contain;
  display: block;
  border-radius: 8px;
}

.brand-typed-line {
  flex: 0 1 100px;
  width: 100px;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
  height: 56px;
  min-height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: inherit;
}

.brand-typed-inner {
  max-width: 100%;
  text-align: center;
}

.brand-typed {
  display: inline;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.25;
  white-space: normal;
  overflow-wrap: break-word;
  word-break: keep-all;
}

/* 커서 막대: 글자(rem) 기준 — 고정 로고와 별개 */
.brand-cursor {
  display: inline-block;
  flex-shrink: 0;
  box-sizing: border-box;
  width: 0.11rem;
  height: 1.05em;
  margin-left: 0.12em;
  border-radius: 0.06rem;
  background-color: var(--color-accent, #38bdf8);
  vertical-align: -0.12em;
  animation: brand-cursor-blink 0.85s step-end infinite;
}

@keyframes brand-cursor-blink {
  50% {
    opacity: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .brand-cursor {
    animation: none;
    opacity: 0.85;
  }
}

.header-search {
  min-width: 0;
  width: 100%;
  max-width: 40rem;
  justify-self: stretch;
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 0.5rem;
}

.header--with-search .header-search {
  max-width: none;
}

/* 입력 + 돋보기 버튼을 한 테두리 안에 */
.header-search-box {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  align-items: stretch;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  overflow: hidden;
  background: var(--color-background);
  box-sizing: border-box;
  transition:
    border-color 0.15s,
    box-shadow 0.15s;
}

.header-search-box:focus-within {
  border-color: rgba(92, 176, 185, 0.55);
  box-shadow: 0 0 0 2px rgba(92, 176, 185, 0.12);
}

.header-search-input {
  box-sizing: border-box;
  flex: 1 1 auto;
  min-width: 6rem;
  width: 0;
  height: 3rem;
  min-height: 3rem;
  padding: 0.65rem 0.85rem;
  font-size: 0.95rem;
  line-height: 1.35;
  border: none;
  border-radius: 0;
  -webkit-appearance: none;
  appearance: none;
  background: transparent;
  color: var(--color-text);
}

.header-search-input:focus {
  outline: none;
}

.header-search-input::placeholder {
  color: var(--color-text);
  opacity: 0.5;
}

.header-search-submit {
  box-sizing: border-box;
  flex: 0 0 auto;
  width: 3.25rem;
  min-width: 3.25rem;
  height: auto;
  min-height: 3rem;
  padding: 0;
  margin: 0;
  border: none;
  border-left: 1px solid var(--color-border);
  border-radius: 0;
  background: var(--color-background-soft);
  color: var(--color-accent);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}

.header-search-submit:hover {
  background: rgba(92, 176, 185, 0.14);
}

.header-search-submit:focus-visible {
  outline: none;
  box-shadow: inset 0 0 0 2px rgba(92, 176, 185, 0.45);
}

.header-search-icon {
  width: 1.35rem;
  height: 1.35rem;
  display: block;
}

.header-search-clear {
  box-sizing: border-box;
  height: 3rem;
  min-height: 3rem;
  padding: 0.65rem 0.85rem;
  font-size: 0.95rem;
  line-height: 1.35;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  min-width: 3.5rem;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
  color: var(--color-text);
  font-weight: 500;
  line-height: 1.25;
  cursor: pointer;
}

/* visibility:hidden은 자리를 유지해 입력+검색이 왼쪽으로 치우쳐 보임 → 숨길 때는 레이아웃에서 제외 */
.header-search-clear--hidden {
  display: none;
  pointer-events: none;
}

.header-search-clear:hover {
  border-color: var(--color-border-hover);
}

.nav {
  min-width: 0;
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 0.45rem 0.6rem;
  font-size: 0.9375rem;
  line-height: 1.35;
  font-weight: 500;
  letter-spacing: -0.01em;
  justify-content: flex-end;
  justify-self: stretch;
  width: 100%;
  overflow: visible;
}

/* 링크·클러스터가 세로로 쪼개지지 않도록 — 좁으면 가로 스크롤 */
.nav :deep(a) {
  flex-shrink: 0;
  white-space: nowrap;
}

.nav > .nav-cluster {
  flex-shrink: 0;
}

/* 프로필·로그아웃을 한 덩어리로 유지 */
.nav-cluster {
  display: inline-flex;
  align-items: center;
  gap: 0.8rem;
  flex-shrink: 0;
  white-space: nowrap;
}

.nav-cluster .user-link {
  max-width: min(13rem, 46vw);
}

.nav-user-dropdown,
.nav-write-dropdown {
  position: relative;
  flex-shrink: 0;
}

/* 트리거와 메뉴 사이로 마우스가 지날 때 :hover가 끊기지 않도록 보이지 않는 연결대 */
.nav-user-dropdown::after,
.nav-write-dropdown::after {
  content: '';
  position: absolute;
  top: 100%;
  right: 0;
  width: max(100%, 9.5rem);
  height: 0.5rem;
  z-index: 199;
}

.nav-user-dropdown-trigger {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  max-width: min(13rem, 46vw);
  padding: 0.15rem 0.3rem 0.15rem 0.2rem;
  margin: -0.15rem -0.3rem -0.15rem -0.2rem;
  border-radius: 8px;
  outline: none;
}

.nav-user-dropdown-trigger:focus-visible {
  outline: 2px solid rgba(92, 176, 185, 0.85);
  outline-offset: 2px;
}

@media (hover: hover) {
  .nav-user-dropdown:hover .nav-user-dropdown-trigger {
    background: rgba(92, 176, 185, 0.08);
  }
}

.nav-user-dropdown-profile-link {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  min-width: 0;
  flex: 1 1 auto;
  max-width: 100%;
  text-decoration: none;
  color: inherit;
  border-radius: 8px;
}

.nav-user-dropdown .nav-user-dropdown-profile-link {
  flex-shrink: 1;
}

.nav-user-dropdown-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  text-decoration: none;
  color: inherit;
  border-radius: 50%;
}

.nav-avatar--ph {
  width: 28px;
  height: 28px;
  box-sizing: border-box;
  font-size: 0.72rem;
  font-weight: 700;
  background: var(--color-background-mute);
  color: var(--color-heading);
  border: 1px solid var(--color-border);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.nav-user-dropdown-caret {
  flex-shrink: 0;
  font-size: 0.62rem;
  opacity: 0.55;
  line-height: 1;
}

.nav-user-dropdown-menu,
.nav-write-dropdown-menu {
  position: absolute;
  top: calc(100% + 0.15rem);
  right: 0;
  z-index: 200;
  min-width: 9.5rem;
  padding: 0.4rem 0;
  margin: 0;
  border-radius: 10px;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.12);
  opacity: 0;
  visibility: hidden;
  transform: translateY(-6px);
  transition:
    opacity 0.1s ease-out,
    transform 0.1s ease-out,
    visibility 0.1s;
  pointer-events: none;
}

.nav-user-dropdown:hover .nav-user-dropdown-menu,
.nav-user-dropdown:focus-within .nav-user-dropdown-menu,
.nav-write-dropdown:hover .nav-write-dropdown-menu,
.nav-write-dropdown:focus-within .nav-write-dropdown-menu {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
  pointer-events: auto;
}

.nav-admin-dropdown-block {
  padding-bottom: 0.35rem;
  margin-bottom: 0.35rem;
  border-bottom: 1px solid var(--color-border);
}

.nav-user-dropdown-item {
  display: block;
  width: 100%;
  box-sizing: border-box;
  padding: 0.48rem 0.95rem;
  font-size: 0.9rem;
  font-weight: 500;
  font-family: inherit;
  color: var(--color-text);
  text-decoration: none;
  white-space: nowrap;
  text-align: left;
  border: none;
  background: none;
  cursor: pointer;
}

.nav-user-dropdown-item:hover {
  background: rgba(92, 176, 185, 0.12);
}

/* 프로필 메뉴 활성 링크와 + 메뉴(판매/구매 현재 위치) 동일 톤 */
.nav-user-dropdown-item.router-link-active,
.nav-write-dropdown-menu .nav-user-dropdown-item.nav-write-menu-item--here {
  color: var(--color-heading);
  font-weight: 600;
}

.nav-user-dropdown-item--logout {
  margin-top: 0.2rem;
  padding-top: 0.55rem;
  border-top: 1px solid var(--color-border);
  color: #c0392b;
  font-weight: 600;
}

.nav-user-dropdown-item--logout:hover {
  background: rgba(192, 57, 43, 0.1);
  color: #a93226;
}

@media (prefers-color-scheme: dark) {
  .nav-user-dropdown-item--logout {
    color: #e74c3c;
  }

  .nav-user-dropdown-item--logout:hover {
    background: rgba(231, 76, 60, 0.15);
    color: #f1948a;
  }
}

.nav-cluster .user-text {
  display: inline-flex;
  align-items: center;
  gap: 0.35em;
  min-width: 0;
  max-width: 100%;
}

.nav-cluster .user-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.nav-write-dropdown-trigger {
  position: relative;
  display: inline-block;
  flex-shrink: 0;
  box-sizing: border-box;
  width: 2.25rem;
  height: 2.25rem;
  padding: 0;
  margin: 0;
  border-radius: 8px;
  font-family: inherit;
  color: #fff;
  background: var(--color-accent);
  border: 1px solid transparent;
  cursor: pointer;
  -webkit-appearance: none;
  appearance: none;
  line-height: 0;
  vertical-align: middle;
  transition: filter 0.15s ease;
}

.nav-write-dropdown-plus {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  line-height: 0;
  transform: rotate(0deg);
  transform-origin: 50% 50%;
  transition: transform 0.42s cubic-bezier(0.34, 1.45, 0.64, 1);
}

/* 텍스트 글리프 대신 viewBox 기준 대칭 SVG — 회전 전·후 모두 기하학적 중앙 유지 */
.nav-write-dropdown-icon {
  display: block;
  width: 1.25rem;
  height: 1.25rem;
  flex-shrink: 0;
}

.nav-write-dropdown-trigger:focus-visible {
  outline: 2px solid rgba(92, 176, 185, 0.85);
  outline-offset: 2px;
}

@media (hover: hover) {
  .nav-write-dropdown:hover .nav-write-dropdown-trigger {
    filter: brightness(1.06);
  }

  .nav-write-dropdown:hover .nav-write-dropdown-plus {
    transform: rotate(45deg);
  }
}

/* 키보드·터치로 메뉴 열린 동안에도 아이콘만 유지 */
.nav-write-dropdown:focus-within .nav-write-dropdown-plus {
  transform: rotate(45deg);
}

@media (prefers-reduced-motion: reduce) {
  .nav-write-dropdown-plus {
    transition: transform 0.18s ease;
  }
}

@media (max-width: 899px) {
  .header {
    padding-inline: 0.75rem;
    box-sizing: border-box;
  }

  .header--with-search {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto;
    justify-items: center;
  }

  .header--no-search {
    grid-template-columns: 1fr;
    justify-items: center;
  }

  .header--no-search .header-brand {
    grid-column: auto;
  }

  .header--with-search .nav {
    justify-self: center;
  }

  .header--no-search .nav {
    grid-column: auto;
    justify-self: center;
    justify-content: center;
  }

  .header-brand {
    justify-self: center;
    width: 100%;
    max-width: 100%;
    display: flex;
    justify-content: center;
  }

  .header--with-search .header-brand {
    width: 100%;
    max-width: 100%;
  }

  /* 검색 줄: 로고처럼 가운데, 폭은 화면에 맞게 */
  .header-search {
    justify-self: center;
    width: min(100%, 40rem);
    max-width: 100%;
    box-sizing: border-box;
  }

  .header--with-search .header-search {
    max-width: min(100%, 40rem);
  }

  /* 네비: 링크 묶음을 가운데 — 줄이 부족하면 다음 줄로(항목 단위) */
  .nav {
    justify-self: center;
    width: 100%;
    max-width: 40rem;
    justify-content: center;
    flex-wrap: wrap;
    row-gap: 0.6rem;
    overflow-x: visible;
    overflow-y: visible;
    padding-inline: 0.25rem;
    box-sizing: border-box;
  }
}

.nav a.router-link-exact-active {
  color: var(--color-heading);
  font-weight: 600;
}

.user {
  font-size: inherit;
  color: var(--color-text);
}

.user-link {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  max-width: 100%;
  text-decoration: none;
  color: inherit;
  border-radius: 8px;
  padding: 0.15rem 0.25rem;
  margin: -0.15rem -0.25rem;
  transition: text-shadow 0.35s ease;
}

@media (hover: hover) {
  .user-link:hover {
    background: transparent;
    text-shadow: var(--link-hover-text-shadow);
  }
}

.nav-avatar {
  flex-shrink: 0;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid var(--color-border);
}

.user-text {
  min-width: 0;
}

.badge {
  flex-shrink: 0;
  padding: 0.1em 0.42em;
  font-size: 0.8125em;
  font-weight: 600;
  line-height: 1.2;
  letter-spacing: -0.02em;
  border-radius: 0.3em;
  background: rgba(92, 176, 185, 0.2);
  color: hsl(186, 38%, 28%);
}

.ghost {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.35rem 0.65rem;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-text);
  font-size: inherit;
  font-weight: inherit;
  line-height: 1.35;
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
  background: var(--color-accent);
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
