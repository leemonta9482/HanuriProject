<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { addFavorite, fetchBoards, removeFavorite, type BoardSort } from '@/api/boards'
import { uploadsPublicUrl } from '@/api/client'
import type { BoardListItem } from '@/api/types'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()

const userId = computed(() => String(route.params.userId ?? '').trim())

const sort = ref<BoardSort>('latest')
const page = ref(1)
const totalPages = ref(0)
const items = ref<BoardListItem[]>([])
const shopOwnerName = ref('')
const shopOwnerAvatar = ref<string | null>(null)
const loading = ref(false)
const error = ref('')
const sentinel = ref<HTMLElement | null>(null)
const favBusyBoardId = ref<number | null>(null)

const hasMore = computed(() => totalPages.value > 0 && page.value <= totalPages.value)

const isOwnShop = computed(() => auth.user?.user_id === userId.value)

function thumbUrl(path: string | null): string | null {
  if (!path) return null
  return uploadsPublicUrl(path)
}

function formatPrice(n: number): string {
  return new Intl.NumberFormat('ko-KR').format(n) + '원'
}

const statusLabel: Record<string, string> = {
  ON_SALE: '판매중',
  RESERVED: '예약중',
  SOLD: '거래완료',
}

async function tryLoadMoreIfSentinelVisible() {
  await nextTick()
  if (!loading.value && !hasMore.value) return
  const el = sentinel.value
  if (!el) return
  const rect = el.getBoundingClientRect()
  const vh = window.innerHeight || document.documentElement.clientHeight
  if (rect.top <= vh + 200) {
    await load(false)
  }
}

async function load(reset: boolean) {
  if (!userId.value) return
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    const p = reset ? 1 : page.value
    const res = await fetchBoards({
      page: p,
      page_size: 12,
      sort: sort.value,
      seller_id: userId.value,
    })
    if (reset) {
      items.value = res.items
    } else {
      items.value = [...items.value, ...res.items]
    }
    totalPages.value = res.pages
    page.value = p + 1
    shopOwnerName.value =
      res.shop_owner_name?.trim() || res.items[0]?.seller_name?.trim() || userId.value
    shopOwnerAvatar.value =
      res.shop_owner_profile_image_path?.trim() ||
      res.items[0]?.seller_profile_image_path?.trim() ||
      null
  } catch (e) {
    error.value = e instanceof Error ? e.message : '목록을 불러오지 못했습니다.'
    if (reset) items.value = []
  } finally {
    loading.value = false
    void tryLoadMoreIfSentinelVisible()
  }
}

watch(sort, () => {
  page.value = 1
  totalPages.value = 0
  void load(true)
})

watch(userId, () => {
  page.value = 1
  totalPages.value = 0
  void load(true)
})

let obs: IntersectionObserver | null = null

onMounted(() => {
  void load(true)
  obs = new IntersectionObserver(
    (entries) => {
      const e = entries[0]
      if (e?.isIntersecting && hasMore.value && !loading.value) {
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
        if (e?.isIntersecting && hasMore.value && !loading.value) {
          void load(false)
        }
      },
      { root: null, rootMargin: '200px', threshold: 0 },
    )
    obs.observe(el)
  }
})

async function onToggleFavorite(it: BoardListItem) {
  if (favBusyBoardId.value === it.board_id) return
  favBusyBoardId.value = it.board_id
  error.value = ''
  try {
    const detail = it.is_favorited
      ? await removeFavorite(it.board_id)
      : await addFavorite(it.board_id)
    const idx = items.value.findIndex((x) => x.board_id === it.board_id)
    const cur = idx >= 0 ? items.value[idx] : undefined
    if (cur) {
      items.value[idx] = {
        ...cur,
        is_favorited: detail.is_favorited,
        favorite_count: detail.favorite_count,
      } satisfies BoardListItem
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '찜 처리에 실패했습니다.'
  } finally {
    favBusyBoardId.value = null
  }
}
</script>

<template>
  <div class="market">
    <header class="toolbar">
      <div class="head-main">
        <div class="shop-identity">
          <div class="shop-avatar">
            <img v-if="shopOwnerAvatar" :src="thumbUrl(shopOwnerAvatar)!" alt="" />
            <span v-else class="ph">{{ shopOwnerName.slice(0, 1) || '?' }}</span>
          </div>
          <div class="shop-titles">
            <h1 class="title">{{ shopOwnerName }}님의 상점</h1>
            <p class="sub">판매 중인 글만 모아 보여요.</p>
          </div>
        </div>
      </div>
      <div class="actions">
        <label class="sort">
          <span class="sr-only">정렬</span>
          <select v-model="sort" class="select-theme">
            <option value="latest">최신순</option>
            <option value="price_asc">가격 낮은순</option>
            <option value="price_desc">가격 높은순</option>
          </select>
        </label>
        <RouterLink v-if="isOwnShop" class="btn primary" to="/my-shop">내 상점 관리</RouterLink>
      </div>
    </header>

    <p v-if="error" class="err" role="alert">{{ error }}</p>

    <ul v-if="!error || items.length" class="grid">
      <li v-for="it in items" :key="it.board_id" class="card-wrap">
        <div class="card">
          <RouterLink :to="`/boards/${it.board_id}`" class="card-link">
            <div class="thumb" :class="{ empty: !it.thumbnail_path }">
              <img v-if="thumbUrl(it.thumbnail_path)" :src="thumbUrl(it.thumbnail_path)!" alt="" />
              <span v-else class="ph">이미지 없음</span>
              <span
                class="badge-status"
                :class="{
                  'badge-status--on-sale': it.status === 'ON_SALE',
                  'badge-status--reserved': it.status === 'RESERVED',
                  'badge-status--sold': it.status === 'SOLD',
                }"
                >{{ statusLabel[it.status] ?? it.status }}</span
              >
              <button
                v-if="!isOwnShop"
                type="button"
                class="thumb-fav"
                :class="{ 'thumb-fav--on': it.is_favorited }"
                :disabled="favBusyBoardId === it.board_id"
                @click.stop.prevent="onToggleFavorite(it)"
              >
                <span class="thumb-fav-count">{{ it.favorite_count }}</span>
                <span class="thumb-fav-icon" aria-hidden="true">{{ it.is_favorited ? '♥' : '♡' }}</span>
              </button>
            </div>
            <div class="meta">
              <p class="card-title">{{ it.title }}</p>
              <p class="price">{{ formatPrice(it.price) }}</p>
            </div>
          </RouterLink>
        </div>
      </li>
    </ul>

    <p v-if="!loading && items.length === 0 && !error" class="empty">등록된 판매글이 없습니다.</p>

    <div ref="sentinel" class="sentinel" aria-hidden="true" />

    <p v-if="loading" class="hint">불러오는 중…</p>
    <p v-if="!loading && !hasMore && items.length > 0" class="hint end">모든 글을 불러왔습니다.</p>
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
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  padding-block: 0.625rem;
  margin-bottom: 2.5rem;
}

.head-main {
  width: 100%;
  min-width: 0;
  display: flex;
  justify-content: center;
}

.shop-identity {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.shop-avatar {
  box-sizing: border-box;
  width: 52px;
  height: 52px;
  min-width: 52px;
  min-height: 52px;
  aspect-ratio: 1;
  border-radius: 50%;
  overflow: hidden;
  border: 1px solid var(--color-border);
  background: var(--color-background-mute);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.shop-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.shop-avatar .ph {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-heading);
  line-height: 1;
}

.shop-titles {
  min-width: 0;
}

.title {
  font-size: 1.35rem;
  font-weight: 700;
  line-height: 1.25;
  color: var(--color-heading);
  margin: 0 0 0.2rem;
  word-break: break-all;
}

.sub {
  margin: 0;
  font-size: 0.88rem;
  color: var(--color-text);
  opacity: 0.85;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.sort {
  display: inline-flex;
  align-items: center;
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

.btn.primary {
  background: var(--color-accent);
  border-color: transparent;
  color: #fff;
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
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
}

.card {
  border: 1px solid var(--color-border);
  border-radius: 12px;
  overflow: hidden;
  background: var(--color-background-soft);
}

.card-link {
  display: block;
  text-decoration: none;
  color: inherit;
}

.thumb {
  aspect-ratio: 4 / 3;
  background: var(--color-background-mute);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.ph {
  font-size: 0.85rem;
  opacity: 0.6;
}

.badge-status {
  position: absolute;
  top: 0.5rem;
  left: 0.5rem;
  padding: 0.15rem 0.45rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
}

.badge-status--on-sale {
  background: hsla(160, 100%, 32%, 0.92);
}

.badge-status--reserved {
  background: rgba(180, 120, 0, 0.9);
}

.badge-status--sold {
  background: rgba(90, 90, 90, 0.88);
}

.thumb-fav {
  position: absolute;
  bottom: 0.45rem;
  right: 0.45rem;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.45rem;
  border: none;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  cursor: pointer;
  font-size: 0.8rem;
}

.thumb-fav--on .thumb-fav-icon {
  color: #e74c3c;
}

.meta {
  padding: 0.65rem 0.75rem 0.85rem;
}

.card-title {
  font-size: 0.92rem;
  font-weight: 600;
  margin: 0 0 0.35rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
}

.price {
  margin: 0;
  font-weight: 700;
  color: hsl(186, 38%, 28%);
}

.empty,
.hint {
  text-align: center;
  padding: 2rem 1rem;
  color: var(--color-text);
}

.hint.end {
  opacity: 0.75;
  font-size: 0.9rem;
}

.sentinel {
  height: 1px;
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
</style>
