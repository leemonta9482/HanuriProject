<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import type { RouteLocationRaw } from 'vue-router'

import { addFavorite, removeFavorite, type BoardSort } from '@/api/boards'
import { fetchFeed } from '@/api/feed'
import { uploadsPublicUrl } from '@/api/client'
import type { FeedItem } from '@/api/types'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()

const sort = ref<BoardSort>('latest')
/** 상단 네비 URL 쿼리 `q`와 동기화 */
const appliedSearch = computed(() => {
  const raw = route.query.q
  const q = Array.isArray(raw) ? raw[0] : raw
  return typeof q === 'string' ? q.trim() : ''
})
const items = ref<FeedItem[]>([])
const page = ref(1)
const totalPages = ref(0)
const loading = ref(false)
const error = ref('')
const sentinel = ref<HTMLElement | null>(null)
const hasMore = computed(() => totalPages.value > 0 && page.value <= totalPages.value)
/** 같은 카드 연속 찜 요청 방지 */
const favBusyBoardId = ref<number | null>(null)

const statusLabel: Record<string, string> = {
  ON_SALE: '판매중',
  RESERVED: '예약중',
  SOLD: '거래완료',
}

/** 비로그인 미리보기 카드 슬롯(12개) */
const mockCardKeys = Array.from({ length: 12 }, (_, i) => i)

function thumbUrl(path: string | null): string | null {
  if (!path) return null
  return uploadsPublicUrl(path)
}

function formatPrice(n: number | null): string {
  if (n == null || Number.isNaN(n)) return '가격 미정'
  return new Intl.NumberFormat('ko-KR').format(n) + '원'
}

function itemLink(it: FeedItem): RouteLocationRaw {
  if (it.kind === 'board' && it.board_id != null) return `/boards/${it.board_id}`
  if (it.kind === 'wanted' && it.wanted_id != null) return `/wanted/${it.wanted_id}`
  return '/'
}

function cardKey(it: FeedItem): string {
  if (it.kind === 'board' && it.board_id != null) return `b-${it.board_id}`
  if (it.kind === 'wanted' && it.wanted_id != null) return `w-${it.wanted_id}`
  return `x-${it.title}`
}

function authorThumb(it: FeedItem): string | null {
  const p = it.author_profile_image_path
  if (!p?.trim()) return null
  return uploadsPublicUrl(p.trim())
}

async function onToggleFeedFavorite(it: FeedItem) {
  if (it.kind !== 'board' || it.board_id == null || it.is_owner) return
  if (favBusyBoardId.value === it.board_id) return
  favBusyBoardId.value = it.board_id
  error.value = ''
  try {
    const detail = it.is_favorited
      ? await removeFavorite(it.board_id)
      : await addFavorite(it.board_id)
    const key = cardKey(it)
    const idx = items.value.findIndex((x) => cardKey(x) === key)
    if (idx >= 0) {
      const cur = items.value[idx]
      if (cur && cur.kind === 'board') {
        items.value[idx] = {
          ...cur,
          is_favorited: detail.is_favorited,
          favorite_count: detail.favorite_count,
        } satisfies FeedItem
      }
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '찜 처리에 실패했습니다.'
  } finally {
    favBusyBoardId.value = null
  }
}

/** IntersectionObserver는 교차 상태가 변할 때만 콜백을 호출한다. 로딩 중에는 스킵되다가,
 *  끝난 뒤에도 센티널이 그대로 보이면(큰 화면·짧은 목록) 추가 로드가 안 될 수 있어 보완한다. */
async function tryLoadMoreIfSentinelVisible() {
  await nextTick()
  if (!auth.isLoggedIn || loading.value) return
  if (!hasMore.value) return
  const el = sentinel.value
  if (!el) return
  const rect = el.getBoundingClientRect()
  const vh = window.innerHeight || document.documentElement.clientHeight
  const margin = 200
  if (rect.top <= vh + margin) {
    await load(false)
  }
}

async function load(reset: boolean) {
  if (!auth.isLoggedIn) {
    items.value = []
    totalPages.value = 0
    page.value = 1
    return
  }
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    const p = reset ? 1 : page.value
    const res = await fetchFeed({
      page: p,
      page_size: 12,
      sort: sort.value,
      q: appliedSearch.value || undefined,
    })
    if (reset) {
      items.value = res.items
    } else {
      items.value = [...items.value, ...res.items]
    }
    totalPages.value = res.pages
    page.value = p + 1
  } catch (e) {
    error.value = e instanceof Error ? e.message : '목록을 불러오지 못했습니다.'
  } finally {
    loading.value = false
    void tryLoadMoreIfSentinelVisible()
  }
}

watch(sort, () => {
  if (!auth.isLoggedIn || route.name !== 'home') return
  page.value = 1
  totalPages.value = 0
  void load(true)
})

watch(
  () => [route.name, route.fullPath, auth.isLoggedIn] as const,
  () => {
    if (route.name !== 'home' || !auth.isLoggedIn) {
      if (!auth.isLoggedIn) {
        items.value = []
        totalPages.value = 0
        page.value = 1
        error.value = ''
      }
      return
    }
    page.value = 1
    totalPages.value = 0
    void load(true)
  },
  { immediate: true },
)

let obs: IntersectionObserver | null = null

onMounted(() => {
  obs = new IntersectionObserver(
    (entries) => {
      const e = entries[0]
      if (
        e?.isIntersecting &&
        auth.isLoggedIn &&
        hasMore.value &&
        !loading.value
      ) {
        void load(false)
      }
    },
    { root: null, rootMargin: '200px', threshold: 0 },
  )
  if (sentinel.value) obs.observe(sentinel.value)
})

watch(sentinel, (el) => {
  obs?.disconnect()
  if (el) {
    obs = new IntersectionObserver(
      (entries) => {
        const e = entries[0]
        if (
          e?.isIntersecting &&
          auth.isLoggedIn &&
          hasMore.value &&
          !loading.value
        ) {
          void load(false)
        }
      },
      { root: null, rootMargin: '200px', threshold: 0 },
    )
    obs.observe(el)
  }
})
</script>

<template>
  <div class="market">
    <header class="toolbar">
      <div class="toolbar-lead" aria-hidden="true" />
      <h1 class="title">중고 거래</h1>
      <div class="toolbar-trail">
        <div v-if="auth.isLoggedIn" class="actions">
          <label class="sort">
            <span class="sr-only">정렬</span>
            <select v-model="sort" class="select-theme">
              <option value="latest">최신순</option>
              <option value="price_asc">가격 낮은순</option>
              <option value="price_desc">가격 높은순</option>
            </select>
          </label>
        </div>
      </div>
    </header>

    <p v-if="error" class="err" role="alert">{{ error }}</p>

    <div v-if="!auth.isLoggedIn" class="login-gate-section">
      <div class="login-gate-blur" aria-hidden="true">
        <ul class="grid">
          <li v-for="i in mockCardKeys" :key="i" class="card-wrap">
            <div class="card-mock login-gate-mock-card">
              <div class="thumb login-gate-mock-thumb" />
              <div class="meta">
                <p class="card-title">중고 상품 제목이 들어갑니다</p>
                <p class="price">12,000원</p>
                <p class="sub">닉네임 · 캠퍼스</p>
              </div>
            </div>
          </li>
        </ul>
      </div>
      <div class="login-gate-float">
        <div class="login-gate">
          <p class="login-gate-title">중고 거래 목록은 로그인 후 확인할 수 있습니다.</p>
          <p class="login-gate-text">같은 학교로 등록된 회원이 올린 판매글·구매 희망글만 보입니다.</p>
          <div class="login-gate-actions">
            <RouterLink class="btn primary" to="/login">로그인</RouterLink>
            <RouterLink class="btn" to="/register">회원가입</RouterLink>
          </div>
        </div>
      </div>
    </div>

    <ul v-else class="grid" aria-label="거래 목록">
      <li v-for="it in items" :key="cardKey(it)" class="card-wrap">
        <div class="card card--feed">
          <RouterLink :to="itemLink(it)" class="card-link">
            <div
              class="thumb"
              :class="{
                empty: !it.thumbnail_path,
                'thumb--wanted': it.kind === 'wanted' && !it.thumbnail_path,
              }"
            >
              <img v-if="thumbUrl(it.thumbnail_path)" :src="thumbUrl(it.thumbnail_path)!" alt="" />
              <span v-else-if="it.kind === 'wanted'" class="wanted-thumb__icon" aria-hidden="true">🔍</span>
              <span v-else class="ph">이미지 없음</span>
              <span
                v-if="it.kind === 'board' && it.status"
                class="badge-status"
                :class="{
                  'badge-status--on-sale': it.status === 'ON_SALE',
                  'badge-status--reserved': it.status === 'RESERVED',
                  'badge-status--sold': it.status === 'SOLD',
                }"
              >{{ statusLabel[it.status] ?? it.status }}</span>
              <span v-if="it.kind === 'wanted'" class="badge-kind">구매 희망</span>
              <button
                v-if="it.kind === 'board' && it.board_id != null && !it.is_owner"
                type="button"
                class="thumb-fav"
                :class="{ 'thumb-fav--on': it.is_favorited }"
                :disabled="favBusyBoardId === it.board_id"
                :aria-pressed="it.is_favorited"
                :aria-label="it.is_favorited ? '찜 해제' : '찜하기'"
                @click.stop.prevent="onToggleFeedFavorite(it)"
              >
                <span class="thumb-fav-count">{{ it.favorite_count }}</span>
                <span class="thumb-fav-icon" aria-hidden="true">{{ it.is_favorited ? '♥' : '♡' }}</span>
              </button>
              <div
                v-else-if="it.kind === 'board' && it.board_id != null && it.is_owner"
                class="thumb-fav thumb-fav--static"
                title="내가 올린 글은 찜할 수 없습니다"
              >
                <span class="thumb-fav-count">{{ it.favorite_count }}</span>
                <span class="thumb-fav-icon" aria-hidden="true">♡</span>
              </div>
            </div>
            <div class="meta">
              <p class="card-title">{{ it.title }}</p>
              <p class="price">{{ formatPrice(it.price) }}</p>
              <p class="sub">{{ it.location || '장소 미정' }}</p>
            </div>
          </RouterLink>
          <div v-if="it.author_user_id" class="seller-bar">
            <RouterLink
              :to="
                it.is_owner
                  ? { name: 'my-shop' }
                  : { name: 'user-shop', params: { userId: it.author_user_id } }
              "
              class="seller-chip"
              @click.stop
            >
              <span class="seller-av-wrap">
                <img v-if="authorThumb(it)" :src="authorThumb(it)!" alt="" class="seller-av" />
                <span v-else class="seller-av seller-av--ph" aria-hidden="true">{{
                  (it.author_name || '?').slice(0, 1)
                }}</span>
              </span>
              <span class="seller-name">{{ it.author_name }}</span>
            </RouterLink>
          </div>
        </div>
      </li>
    </ul>

    <p v-if="auth.isLoggedIn && !loading && items.length === 0 && !error" class="empty">
      {{ appliedSearch.length ? '검색 결과가 없습니다.' : '등록된 게시글이 없습니다.' }}
    </p>

    <div v-if="auth.isLoggedIn" ref="sentinel" class="sentinel" aria-hidden="true" />

    <p v-if="auth.isLoggedIn && loading" class="hint">불러오는 중…</p>
    <p v-if="auth.isLoggedIn && !hasMore && items.length > 0" class="hint end">
      모든 게시글을 불러왔습니다.
    </p>
  </div>
</template>

<style scoped>
.market {
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 0.5rem 2rem;
}

.toolbar {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  /* 정렬 셀렉트가 더 높아도 제목은 상단 기준(찜/내상점과 같은 시각적 높이) */
  align-items: start;
  gap: 0.5rem 1rem;
  /* 메인 헤더와 본문 사이 간격(2.5rem)과 맞춤 */
  padding-block: 0.625rem;
  margin-bottom: 2.5rem;
}

.toolbar-lead {
  min-width: 0;
}

.toolbar-trail {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  min-width: 0;
}

.title {
  margin: 0;
  text-align: center;
  justify-self: center;
  font-size: 1.35rem;
  font-weight: 700;
  line-height: 1.25;
  color: var(--color-heading);
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
  justify-content: flex-end;
}

@media (max-width: 480px) {
  .toolbar {
    grid-template-columns: 1fr;
    row-gap: 0.75rem;
  }

  .toolbar-lead {
    display: none;
  }

  .title {
    text-align: center;
  }

  .toolbar-trail {
    width: 100%;
  }
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.45rem 0.85rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
  color: var(--color-text);
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
}

.btn:hover {
  border-color: var(--color-border-hover);
}

.btn.primary {
  background: var(--color-accent);
  border-color: transparent;
  color: #fff;
}

.btn.primary:hover {
  filter: brightness(1.05);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}

.err {
  color: #c0392b;
  margin-bottom: 1rem;
}

.grid {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

/* 태블릿·모바일: 카드 폭을 줄여 한 줄에 2개 */
@media (max-width: 1024px) {
  .grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.65rem;
  }
}

@media (max-width: 480px) {
  .grid {
    gap: 0.5rem;
  }

  .card-title {
    font-size: 0.88rem;
  }

  .price {
    font-size: 0.92rem;
  }

  .sub {
    font-size: 0.74rem;
  }

  .meta {
    padding: 0.5rem 0.55rem 0.65rem;
  }
}

.card-wrap {
  min-width: 0;
}

.card-mock {
  display: block;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
  height: 100%;
}

.card--feed {
  display: flex;
  flex-direction: column;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
  height: 100%;
  transition:
    box-shadow 0.2s,
    transform 0.15s;
}

.card-link {
  display: block;
  text-decoration: none;
  color: inherit;
  flex: 1 1 auto;
  min-height: 0;
}

.card--feed:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.seller-bar {
  flex-shrink: 0;
  border-top: 1px solid var(--color-border);
  padding: 0.4rem 0.55rem;
  background: var(--color-background);
}

.seller-chip {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  text-decoration: none;
  color: var(--color-text);
  font-size: 0.82rem;
  font-weight: 500;
  border-radius: 8px;
  padding: 0.15rem 0.2rem;
  margin: -0.15rem -0.2rem;
  transition: background 0.15s;
}

.seller-chip:hover {
  background: rgba(92, 176, 185, 0.12);
}

.seller-av {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid var(--color-border);
  vertical-align: middle;
}

.seller-av--ph {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  font-weight: 700;
  background: var(--color-background-mute);
  color: var(--color-heading);
}

.seller-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.thumb {
  position: relative;
  aspect-ratio: 4 / 3;
  background: var(--color-background-mute);
  overflow: hidden;
}

.thumb.empty {
  display: flex;
  align-items: center;
  justify-content: center;
}

.thumb.thumb--wanted {
  background: linear-gradient(
    145deg,
    rgba(var(--color-accent-rgb), 0.28) 0%,
    rgba(var(--color-accent-rgb), 0.08) 50%,
    var(--color-background-mute) 100%
  );
}

.wanted-thumb__icon {
  font-size: 2rem;
  line-height: 1;
  opacity: 0.9;
}

.thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.ph {
  font-size: 0.85rem;
  color: var(--color-text);
  opacity: 0.7;
}

.badge-status {
  position: absolute;
  left: 0.5rem;
  top: 0.5rem;
  padding: 0.15rem 0.45rem;
  font-size: 0.72rem;
  font-weight: 600;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
}

.badge-status--on-sale {
  background: hsla(160, 100%, 32%, 0.92);
  color: #fff;
}

.badge-status--reserved {
  background: hsla(45, 96%, 48%, 0.95);
  color: hsl(28, 85%, 16%);
}

.badge-status--sold {
  background: hsla(0, 65%, 44%, 0.95);
  color: #fff;
}

.badge-kind {
  position: absolute;
  left: 0.5rem;
  top: 0.5rem;
  padding: 0.15rem 0.45rem;
  font-size: 0.72rem;
  font-weight: 600;
  border-radius: 6px;
  background: hsla(200, 70%, 35%, 0.92);
  color: #fff;
}

.thumb-fav {
  position: absolute;
  right: 0.45rem;
  bottom: 0.45rem;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.12rem;
  min-width: 2.35rem;
  padding: 0.28rem 0.35rem 0.22rem;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  background: rgba(0, 0, 0, 0.48);
  color: #fff;
  line-height: 1;
  transition:
    background 0.15s,
    transform 0.12s;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.thumb-fav:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.62);
  transform: scale(1.04);
}

.thumb-fav:disabled {
  opacity: 0.65;
  cursor: wait;
}

.thumb-fav--static {
  cursor: default;
  pointer-events: none;
  opacity: 0.88;
}

.thumb-fav--on .thumb-fav-icon {
  color: #ff6b8a;
}

.thumb-fav-count {
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.45);
}

.thumb-fav-icon {
  font-size: 1.05rem;
  line-height: 1;
  transition: color 0.15s;
}

.meta {
  padding: 0.65rem 0.75rem 0.85rem;
}

.card-title {
  font-weight: 600;
  font-size: 0.95rem;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.price {
  margin-top: 0.35rem;
  font-weight: 700;
  font-size: 1rem;
  color: var(--color-heading);
}

.sub {
  margin-top: 0.25rem;
  font-size: 0.8rem;
  opacity: 0.85;
}

.sentinel {
  height: 1px;
}

.hint {
  text-align: center;
  font-size: 0.9rem;
  color: var(--color-text);
  opacity: 0.8;
  margin-top: 1rem;
}

.hint.end {
  opacity: 0.6;
}

.empty {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--color-text);
  opacity: 0.85;
}

.login-gate-section {
  position: relative;
  width: 100%;
}

/* 실제 `.grid`·`.card`와 동일한 레이아웃; 블러만 적용 */
.login-gate-blur {
  filter: blur(9px);
  pointer-events: none;
  user-select: none;
}

.login-gate-blur .login-gate-mock-card:hover {
  box-shadow: none;
  transform: none;
}

.login-gate-blur .login-gate-mock-thumb {
  background:rgb(184, 184, 184)
}

.login-gate-float {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 1rem;
  pointer-events: none;
}

.login-gate {
  pointer-events: auto;
  padding: clamp(1.75rem, 4vw, 2.5rem) clamp(1.25rem, 4vw, 2rem);
  text-align: center;
  border-radius: 14px;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  max-width: min(440px, 100%);
}

.login-gate-title {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--color-heading);
  margin-bottom: 0.5rem;
}

.login-gate-text {
  font-size: 0.92rem;
  color: var(--color-text);
  opacity: 0.9;
  margin-bottom: 1.25rem;
  line-height: 1.5;
}

.login-gate-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
}

</style>
