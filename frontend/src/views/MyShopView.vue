<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import { deleteBoard, fetchMyBoards, updateBoardStatus } from '@/api/boards'
import { uploadsPublicUrl } from '@/api/client'
import { deleteWanted, fetchMyWanted } from '@/api/wanted'
import type { BoardListItem, BoardStatus, WantedPost } from '@/api/types'

const page = ref(1)
const pageSize = ref(12)
const total = ref(0)
const pages = ref(0)
const items = ref<BoardListItem[]>([])
const loading = ref(true)
const error = ref('')
const statusFilter = ref<string>('')
const statusDraft = reactive<Record<number, BoardStatus>>({})
const busyId = ref<number | null>(null)

const wantedItems = ref<WantedPost[]>([])
const wantedPage = ref(1)
const wantedPages = ref(0)
const wantedTotal = ref(0)
const loadingWanted = ref(true)
const wantedBusyId = ref<number | null>(null)

const statusLabel: Record<BoardStatus, string> = {
  ON_SALE: '판매중',
  RESERVED: '예약중',
  SOLD: '거래완료',
}

const statusSelectClass: Record<BoardStatus, string> = {
  ON_SALE: 'select-theme--status-on-sale',
  RESERVED: 'select-theme--status-reserved',
  SOLD: 'select-theme--status-sold',
}

const statusBadgeClass: Record<BoardStatus, string> = {
  ON_SALE: 'badge--on-sale',
  RESERVED: 'badge--reserved',
  SOLD: 'badge--sold',
}

function thumbUrl(path: string | null): string | null {
  if (!path) return null
  return uploadsPublicUrl(path)
}

function formatPrice(n: number): string {
  return new Intl.NumberFormat('ko-KR').format(n) + '원'
}

function formatWantedMaxPrice(n: number | null): string {
  if (n == null || Number.isNaN(n)) return '희망가 미정'
  return '희망 ' + new Intl.NumberFormat('ko-KR').format(n) + '원 이하'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const res = await fetchMyBoards({
      page: page.value,
      page_size: pageSize.value,
      status: statusFilter.value || undefined,
    })
    items.value = res.items
    total.value = res.total
    pages.value = res.pages
    for (const it of res.items) {
      statusDraft[it.board_id] = it.status
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '목록을 불러오지 못했습니다.'
    items.value = []
  } finally {
    loading.value = false
  }
}

async function loadWanted() {
  loadingWanted.value = true
  try {
    const res = await fetchMyWanted({
      page: wantedPage.value,
      page_size: pageSize.value,
    })
    wantedItems.value = res.items
    wantedTotal.value = res.total
    wantedPages.value = res.pages
  } catch {
    wantedItems.value = []
    wantedTotal.value = 0
    wantedPages.value = 0
  } finally {
    loadingWanted.value = false
  }
}

async function removeWanted(w: WantedPost) {
  if (!confirm(`「${w.title}」구매 희망글을 삭제할까요?`)) return
  wantedBusyId.value = w.wanted_id
  try {
    await deleteWanted(w.wanted_id)
    await loadWanted()
  } catch {
    /* ignore */
  } finally {
    wantedBusyId.value = null
  }
}

function prevWantedPage() {
  if (wantedPage.value > 1) wantedPage.value -= 1
}

function nextWantedPage() {
  if (wantedPages.value && wantedPage.value < wantedPages.value) wantedPage.value += 1
}

onMounted(() => {
  void load()
  void loadWanted()
})

watch(page, () => load())

watch(wantedPage, () => loadWanted())

function onFilterChange() {
  page.value = 1
  load()
}

function onPageSizeChange() {
  page.value = 1
  wantedPage.value = 1
  void load()
  void loadWanted()
}

function prevPage() {
  if (page.value > 1) page.value -= 1
}

function nextPage() {
  if (pages.value && page.value < pages.value) page.value += 1
}

async function saveStatus(boardId: number) {
  const row = items.value.find((x) => x.board_id === boardId)
  if (!row) return
  const next = statusDraft[boardId]
  if (next === undefined || next === row.status) return
  busyId.value = boardId
  error.value = ''
  try {
    await updateBoardStatus(boardId, next)
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '상태 변경에 실패했습니다.'
  } finally {
    busyId.value = null
  }
}

async function removeBoard(it: BoardListItem) {
  if (!confirm(`「${it.title}」글을 삭제할까요?`)) return
  busyId.value = it.board_id
  error.value = ''
  try {
    await deleteBoard(it.board_id)
    await load()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '삭제에 실패했습니다.'
  } finally {
    busyId.value = null
  }
}
</script>

<template>
  <div class="market">
    <header class="toolbar">
      <div class="toolbar-lead" aria-hidden="true" />
      <h1 class="title">내 상점</h1>
      <div class="toolbar-trail" />
    </header>

    <h2 class="section-title">판매글</h2>

    <div class="filters">
      <div class="filters-left">
        <label class="filter">
          <span class="filter-label">상태</span>
          <select v-model="statusFilter" class="select-theme" @change="onFilterChange">
            <option value="">전체</option>
            <option value="ON_SALE">판매중</option>
            <option value="RESERVED">예약중</option>
            <option value="SOLD">거래완료</option>
          </select>
        </label>
        <span v-if="!loading" class="filter-meta"
          >총 <strong>{{ total }}</strong
          >건 · {{ page }} / {{ pages || 1 }} 페이지</span
        >
      </div>
      <label class="psize">
        <span class="psize-label">페이지당</span>
        <select v-model.number="pageSize" class="select-theme select-theme--compact" @change="onPageSizeChange">
          <option :value="12">12</option>
          <option :value="24">24</option>
          <option :value="48">48</option>
        </select>
      </label>
    </div>

    <p v-if="loading">불러오는 중…</p>
    <p v-else-if="error" class="err">{{ error }}</p>
    <ul v-else class="grid">
      <li v-for="it in items" :key="it.board_id" class="card-wrap">
        <RouterLink :to="`/boards/${it.board_id}`" class="card">
          <div class="thumb" :class="{ empty: !it.thumbnail_path }">
            <img v-if="thumbUrl(it.thumbnail_path)" :src="thumbUrl(it.thumbnail_path)!" alt="" />
            <span v-else class="ph">이미지 없음</span>
          </div>
          <div class="meta">
            <p class="card-title">{{ it.title }}</p>
            <p class="price">{{ formatPrice(it.price) }}</p>
            <p class="status-line">
              <span class="badge" :class="statusBadgeClass[it.status]">{{ statusLabel[it.status] }}</span>
              <span v-if="it.favorite_count > 0" class="fav">♥ {{ it.favorite_count }}</span>
            </p>
          </div>
        </RouterLink>
        <div class="manage">
          <label class="status-wrap">
            <span class="sr-only">거래 상태</span>
            <select
              v-model="statusDraft[it.board_id]"
              class="select-theme select-theme--compact"
              :class="statusSelectClass[statusDraft[it.board_id] ?? it.status]"
              :disabled="busyId === it.board_id"
              @change="saveStatus(it.board_id)"
            >
              <option value="ON_SALE">판매중</option>
              <option value="RESERVED">예약중</option>
              <option value="SOLD">거래완료</option>
            </select>
          </label>
          <RouterLink class="btn-sm" :to="{ name: 'board-edit', params: { id: String(it.board_id) } }"
            >수정</RouterLink
          >
          <button
            type="button"
            class="btn-sm danger"
            :disabled="busyId === it.board_id"
            @click="removeBoard(it)"
          >
            삭제
          </button>
        </div>
      </li>
    </ul>

    <div v-if="!loading && !error && items.length > 0" class="pager-bar">
      <div class="pager-btns">
        <button type="button" class="btn ghost" :disabled="page <= 1 || loading" @click="prevPage">
          이전
        </button>
        <button
          type="button"
          class="btn ghost"
          :disabled="!pages || page >= pages || loading"
          @click="nextPage"
        >
          다음
        </button>
      </div>
    </div>

    <p v-if="!loading && !error && items.length === 0" class="empty">등록한 판매글이 없습니다.</p>

    <h2 id="my-shop-wanted" class="section-title section-title--spaced" tabindex="-1">구매 희망</h2>
    <p v-if="!loadingWanted" class="wanted-meta">
      총 <strong>{{ wantedTotal }}</strong
      >건 · {{ wantedPage }} / {{ wantedPages || 1 }} 페이지
    </p>

    <p v-if="loadingWanted">불러오는 중…</p>
    <ul v-else class="grid grid--wanted">
      <li v-for="w in wantedItems" :key="w.wanted_id" class="card-wrap">
        <RouterLink :to="`/wanted/${w.wanted_id}`" class="card card--wanted">
          <div class="thumb thumb--wanted" aria-hidden="true">
            <span class="wanted-thumb__icon">🔍</span>
            <span class="wanted-thumb__badge">구매 희망</span>
          </div>
          <div class="meta">
            <p class="card-title">{{ w.title }}</p>
            <p class="price">{{ formatWantedMaxPrice(w.max_price) }}</p>
            <p class="sub">{{ w.preferred_location?.trim() || '장소 미정' }}</p>
          </div>
        </RouterLink>
        <div class="manage">
          <button
            type="button"
            class="btn-sm danger"
            :disabled="wantedBusyId === w.wanted_id"
            @click="removeWanted(w)"
          >
            삭제
          </button>
        </div>
      </li>
    </ul>

    <div v-if="!loadingWanted && wantedItems.length > 0" class="pager-bar pager-bar--wanted">
      <div class="pager-btns">
        <button
          type="button"
          class="btn ghost"
          :disabled="wantedPage <= 1 || loadingWanted"
          @click="prevWantedPage"
        >
          이전
        </button>
        <button
          type="button"
          class="btn ghost"
          :disabled="!wantedPages || wantedPage >= wantedPages || loadingWanted"
          @click="nextWantedPage"
        >
          다음
        </button>
      </div>
    </div>

    <p v-if="!loadingWanted && wantedItems.length === 0" class="empty empty--wanted">
      등록한 구매 희망글이 없습니다.
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
  align-items: center;
  gap: 0.5rem 1rem;
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

.psize {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.85rem;
  color: var(--color-text);
}

.psize-label {
  white-space: nowrap;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
  justify-content: center;
  width: 100%;
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
  font-size: 0.9rem;
  text-decoration: none;
  cursor: pointer;
}

.btn.primary {
  background: var(--color-accent);
  border-color: transparent;
  color: #fff;
  font-weight: 600;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem 1.5rem;
  width: 100%;
  margin-bottom: 1.25rem;
  box-sizing: border-box;
}

.filters-left {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem;
  min-width: 0;
}

.filter-meta {
  font-size: 0.9rem;
  color: var(--color-text);
}

.filters .psize {
  flex: 0 0 auto;
}

.filter {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-label {
  font-size: 0.85rem;
  color: var(--color-text);
}

.err {
  color: #a93226;
  margin-bottom: 1rem;
}

.grid {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1.25rem;
}

.card-wrap {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-height: 0;
  height: 100%;
}

.card {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-height: 0;
  text-decoration: none;
  color: inherit;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  overflow: hidden;
  background: var(--color-background-soft);
  transition: border-color 0.15s;
}

.card:hover {
  border-color: rgba(92, 176, 185, 0.45);
}

.thumb {
  flex: 0 0 auto;
  aspect-ratio: 4 / 3;
  width: 100%;
  background: var(--color-background-mute);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumb.empty .ph {
  font-size: 0.85rem;
  color: var(--color-text);
  opacity: 0.6;
}

.card .meta {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  padding: 0.65rem 0.75rem 0.75rem;
  min-height: 5.75rem;
  box-sizing: border-box;
}

.card-title {
  font-size: 0.92rem;
  font-weight: 600;
  margin: 0 0 0.35rem;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.price {
  margin: 0;
  font-weight: 700;
  color: hsl(186, 38%, 28%);
  font-size: 0.95rem;
}

.status-line {
  margin: 0.35rem 0 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
}

.sub {
  margin: 0.35rem 0 0;
  font-size: 0.8rem;
  line-height: 1.35;
  color: var(--color-text);
  opacity: 0.85;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.badge {
  padding: 0.1rem 0.4rem;
  border-radius: 6px;
  font-size: 0.72rem;
  font-weight: 600;
  color: #fff;
}

.badge--on-sale {
  background: hsla(160, 100%, 32%, 0.92);
  color: #fff;
}

.badge--reserved {
  background: hsla(45, 96%, 48%, 0.95);
  color: hsl(28, 85%, 16%);
}

.badge--sold {
  background: hsla(0, 65%, 44%, 0.95);
  color: #fff;
}

.fav {
  opacity: 0.85;
}

.manage {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem;
}

.status-wrap {
  flex: 1 1 auto;
  min-width: 0;
}

.status-wrap .select-theme {
  width: 100%;
}

.btn-sm {
  flex: 0 0 auto;
  padding: 0.35rem 0.55rem;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
  font-size: 0.82rem;
  text-decoration: none;
  text-align: center;
  cursor: pointer;
}

.btn-sm.danger {
  border-color: rgba(192, 57, 43, 0.45);
  color: #a93226;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.pager-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
}

.pager-btns {
  display: flex;
  gap: 0.5rem;
}

.pager-btns .btn.ghost {
  padding: 0.4rem 0.75rem;
}

.pager-btns .btn.ghost {
  background: transparent;
}

.pager-btns .btn.ghost:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.section-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--color-heading);
  margin: 0 0 0.75rem;
  padding-bottom: 0.35rem;
  border-bottom: 1px solid var(--color-border);
}

.section-title--spaced {
  margin-top: 2.35rem;
}

#my-shop-wanted {
  scroll-margin-top: 5rem;
}

.wanted-meta {
  font-size: 0.9rem;
  margin: 0 0 1rem;
  color: var(--color-text);
}

.card--wanted {
  transition:
    box-shadow 0.2s,
    transform 0.15s;
}

.card--wanted:hover {
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.thumb--wanted {
  position: relative;
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

.wanted-thumb__badge {
  position: absolute;
  left: 0.45rem;
  top: 0.45rem;
  padding: 0.12rem 0.4rem;
  font-size: 0.68rem;
  font-weight: 600;
  border-radius: 6px;
  background: hsla(186, 42%, 22%, 0.88);
  color: #fff;
}

.pager-bar--wanted {
  margin-top: 1rem;
}

.empty--wanted {
  padding-top: 1rem;
}

.empty {
  text-align: center;
  padding: 2rem;
  color: var(--color-text);
  opacity: 0.85;
}
</style>
