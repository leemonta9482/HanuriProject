<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import { deleteAdminBoard, fetchAdminBoards, patchAdminBoard } from '@/api/admin'
import type { AdminBoard } from '@/api/types'

const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const pages = ref(0)
const items = ref<AdminBoard[]>([])
const loading = ref(false)
const listError = ref('')
const savingId = ref<number | null>(null)
const statusDraft = reactive<Record<number, string>>({})

const boardSearchBy = ref<'board_id' | 'title' | 'user_id' | 'author_name'>('title')
const boardSearchQuery = ref('')

const boardSearchPlaceholder = computed(() => {
  switch (boardSearchBy.value) {
    case 'board_id':
      return '게시글 번호(숫자, 정확히 일치)'
    case 'title':
      return '제목 검색'
    case 'user_id':
      return '작성자 아이디'
    case 'author_name':
      return '작성자 이름(실명)'
    default:
      return ''
  }
})

async function load() {
  listError.value = ''
  loading.value = true
  try {
    const q = boardSearchQuery.value.trim()
    const filters: {
      board_id?: number
      title?: string
      user_id?: string
      author_name?: string
    } = {}
    if (q) {
      if (boardSearchBy.value === 'board_id') {
        const n = Number(q)
        if (Number.isFinite(n)) filters.board_id = n
      } else if (boardSearchBy.value === 'title') {
        filters.title = q
      } else if (boardSearchBy.value === 'user_id') {
        filters.user_id = q
      } else {
        filters.author_name = q
      }
    }
    const data = await fetchAdminBoards(page.value, pageSize.value, filters)
    items.value = data.items
    total.value = data.total
    pages.value = data.pages
    for (const b of data.items) {
      statusDraft[b.board_id] = b.status
    }
  } catch (e) {
    listError.value = e instanceof Error ? e.message : '목록을 불러오지 못했습니다.'
    items.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => load())
watch(page, () => load())

function onPageSizeChange() {
  page.value = 1
  load()
}

function onSearch() {
  page.value = 1
  load()
}

function onReset() {
  boardSearchBy.value = 'title'
  boardSearchQuery.value = ''
  onSearch()
}

function prevPage() {
  if (page.value > 1) page.value -= 1
}

function nextPage() {
  if (pages.value && page.value < pages.value) page.value += 1
}

const statusLabel: Record<string, string> = {
  ON_SALE: '판매중',
  RESERVED: '예약중',
  SOLD: '거래완료',
}

async function saveStatus(boardId: number) {
  const row = items.value.find((x) => x.board_id === boardId)
  if (!row) return
  const next = statusDraft[boardId]
  if (next === row.status) return
  savingId.value = boardId
  listError.value = ''
  try {
    await patchAdminBoard(boardId, {
      status: next as 'ON_SALE' | 'RESERVED' | 'SOLD',
    })
    await load()
  } catch (e) {
    listError.value = e instanceof Error ? e.message : '상태 저장 실패'
  } finally {
    savingId.value = null
  }
}

async function removeBoard(b: AdminBoard) {
  if (!confirm(`게시글 #${b.board_id} 「${b.title}」을(를) 삭제할까요?`)) return
  savingId.value = b.board_id
  listError.value = ''
  try {
    await deleteAdminBoard(b.board_id)
    await load()
  } catch (e) {
    listError.value = e instanceof Error ? e.message : '삭제 실패'
  } finally {
    savingId.value = null
  }
}
</script>

<template>
  <div class="admin">
    <nav class="tabs">
      <RouterLink class="tab" to="/admin/users">회원관리</RouterLink>
      <RouterLink class="tab" to="/admin/boards">게시글관리</RouterLink>
      <RouterLink class="tab" to="/admin/reports">신고관리</RouterLink>
    </nav>

    <header class="head">
      <h1 class="h1">게시글 관리</h1>
      <p class="sub">게시글을 조회·검색하고, 거래 상태를 변경하거나 삭제할 수 있습니다.</p>
    </header>

    <div v-if="listError" class="banner err" role="alert">{{ listError }}</div>

    <div class="search">
      <label class="s search-combo">
        <span>검색</span>
        <div class="search-row">
          <select v-model="boardSearchBy" class="select-theme" aria-label="검색 항목">
            <option value="board_id">게시글 번호</option>
            <option value="title">게시글 이름</option>
            <option value="user_id">작성자 아이디</option>
            <option value="author_name">작성자 이름</option>
          </select>
          <input
            v-model="boardSearchQuery"
            type="search"
            class="search-input"
            :placeholder="boardSearchPlaceholder"
            maxlength="200"
            autocomplete="off"
            @keydown.enter.prevent="onSearch"
          />
        </div>
      </label>
      <div class="s search-actions">
        <button type="button" class="btn ghost" :disabled="loading" @click="onReset">초기화</button>
        <button type="button" class="btn primary" :disabled="loading" @click="onSearch">검색</button>
      </div>
    </div>

    <div class="toolbar">
      <span class="meta"
        >총 <strong>{{ total }}</strong
        >개 · 페이지 {{ page }} / {{ pages || 1 }}</span
      >
      <div class="pager">
        <label class="psize"
          >페이지당
          <select v-model.number="pageSize" class="select-theme select-theme--compact" @change="onPageSizeChange">
            <option :value="10">10</option>
            <option :value="20">20</option>
            <option :value="50">50</option>
          </select>
        </label>
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

    <div class="table-wrap">
      <table class="table">
        <colgroup>
          <col class="col-id" />
          <col class="col-title" />
          <col class="col-author" />
          <col class="col-price" />
          <col class="col-status" />
          <col class="col-manage" />
        </colgroup>
        <thead>
          <tr>
            <th scope="col" class="th-num">번호</th>
            <th scope="col">제목</th>
            <th scope="col">작성자</th>
            <th scope="col" class="th-price">가격</th>
            <th scope="col">상태</th>
            <th scope="col" class="th-manage">관리</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="6" class="empty">불러오는 중…</td>
          </tr>
          <tr v-else-if="!items.length">
            <td colspan="6" class="empty">게시글이 없습니다.</td>
          </tr>
          <tr v-for="b in items" :key="b.board_id">
            <td class="mono cell-id">{{ b.board_id }}</td>
            <td class="cell-title">{{ b.title }}</td>
            <td class="mono cell-author">{{ b.user_id }}</td>
            <td class="cell-price">{{ b.price.toLocaleString() }}</td>
            <td class="cell-status">
              <span
                class="status-label"
                :class="{
                  'status-label--on-sale': b.status === 'ON_SALE',
                  'status-label--reserved': b.status === 'RESERVED',
                  'status-label--sold': b.status === 'SOLD',
                }"
              >{{ statusLabel[b.status] ?? b.status }}</span>
            </td>
            <td class="cell-manage">
              <div class="manage-stack">
                <RouterLink class="link-detail" :to="`/boards/${b.board_id}`" target="_blank">상세 보기</RouterLink>
                <div class="status-row">
                  <select
                    v-model="statusDraft[b.board_id]"
                    class="select-theme select-theme--compact"
                    :disabled="savingId === b.board_id"
                  >
                    <option value="ON_SALE">판매중</option>
                    <option value="RESERVED">예약중</option>
                    <option value="SOLD">거래완료</option>
                  </select>
                  <button
                    type="button"
                    class="btn ghost sm"
                    :disabled="savingId === b.board_id || statusDraft[b.board_id] === b.status"
                    @click="saveStatus(b.board_id)"
                  >
                    적용
                  </button>
                </div>
                <button
                  type="button"
                  class="btn danger sm btn-block"
                  :disabled="savingId === b.board_id"
                  @click="removeBoard(b)"
                >
                  삭제
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.admin {
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
}

.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.tab {
  padding: 0.45rem 0.85rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
  color: var(--color-text);
  font-size: 0.9rem;
}

.tab.router-link-active {
  background: hsla(160, 100%, 37%, 0.12);
  border-color: hsla(160, 100%, 37%, 0.35);
  font-weight: 600;
}

.head {
  margin-bottom: 1.25rem;
}

.h1 {
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--color-heading);
  margin-bottom: 0.35rem;
}

.sub {
  font-size: 0.9rem;
  color: var(--color-text);
  opacity: 0.9;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.meta {
  font-size: 0.9rem;
}

.pager {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.pager .psize {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.search {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0.65rem 0.75rem;
  margin-bottom: 1rem;
}

.search-combo {
  flex: 1 1 18rem;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.8rem;
}

.search-row {
  display: flex;
  align-items: stretch;
  gap: 0;
  min-width: 0;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  overflow: hidden;
  background: var(--color-background);
}

.search-row .select-theme {
  flex: 0 0 auto;
}

.search-input {
  flex: 1 1 auto;
  min-width: 0;
  padding: 0.5rem 0.65rem;
  border: none;
  background: var(--color-background);
  color: var(--color-text);
  font-size: 0.92rem;
  box-sizing: border-box;
}

.search-input:focus,
.search-row select:focus {
  outline: none;
}

.search-row:focus-within {
  box-shadow: 0 0 0 2px hsla(160, 100%, 37%, 0.2);
  border-color: hsla(160, 100%, 37%, 0.45);
}

.search-actions {
  display: flex;
  flex-wrap: nowrap;
  gap: 0.5rem;
  align-items: center;
  flex: 0 0 auto;
  margin-left: auto;
  padding-bottom: 0.05rem;
}

.table-wrap {
  overflow-x: auto;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  background: var(--color-background-soft);
  -webkit-overflow-scrolling: touch;
}

.table {
  width: 100%;
  min-width: 860px;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 0.875rem;
}

.table col.col-id {
  width: 7%;
}
.table col.col-title {
  width: 26%;
}
.table col.col-author {
  width: 12%;
}
.table col.col-price {
  width: 10%;
}
.table col.col-status {
  width: 10%;
}
.table col.col-manage {
  width: 35%;
}

.table th,
.table td {
  padding: 0.65rem 0.75rem;
  text-align: left;
  vertical-align: middle;
  border-bottom: 1px solid var(--color-border);
  box-sizing: border-box;
}

.table th {
  font-weight: 600;
  background: var(--color-background-mute);
  white-space: nowrap;
}

.table td {
  word-break: break-word;
}

.th-num {
  text-align: center;
}

.th-price {
  text-align: right;
}

.th-manage {
  text-align: left;
}

.mono {
  font-family: ui-monospace, monospace;
  font-size: 0.8rem;
}

.cell-id {
  text-align: center;
  vertical-align: middle;
}

.cell-title {
  min-width: 0;
  vertical-align: middle;
}

.cell-author {
  vertical-align: middle;
}

.cell-price {
  text-align: right;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  vertical-align: middle;
}

.cell-status {
  vertical-align: middle;
  white-space: nowrap;
}

.cell-manage {
  vertical-align: middle;
}

.empty {
  text-align: center;
  padding: 2rem !important;
  color: var(--color-text);
  opacity: 0.8;
}

.btn {
  padding: 0.45rem 0.9rem;
  border-radius: 8px;
  border: none;
  font-size: 0.875rem;
  cursor: pointer;
}

.btn.primary {
  background: hsla(160, 100%, 37%, 1);
  color: #fff;
  font-weight: 600;
}

.btn.ghost {
  background: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-text);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.banner {
  padding: 0.65rem 0.85rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.banner.err {
  background: rgba(192, 57, 43, 0.12);
  color: #a93226;
}

.manage-stack {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 0.5rem;
  max-width: 100%;
}

.link-detail {
  display: block;
  text-align: center;
  padding: 0.35rem 0.5rem;
  font-size: 0.82rem;
  font-weight: 600;
  color: hsla(160, 100%, 30%, 1);
  text-decoration: none;
  border-radius: 6px;
  background: hsla(160, 100%, 37%, 0.1);
}

.link-detail:hover {
  background: hsla(160, 100%, 37%, 0.18);
}

.status-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  min-width: 0;
}

.status-row .select-theme {
  flex: 1 1 auto;
  min-width: 0;
}

.status-label {
  display: inline-block;
  padding: 0.2rem 0.55rem;
  font-size: 0.8rem;
  font-weight: 600;
  border-radius: 6px;
}

.status-label--on-sale {
  background: hsla(160, 45%, 92%, 1);
  color: hsla(160, 100%, 22%, 1);
}

.status-label--reserved {
  background: hsla(48, 88%, 88%, 1);
  color: hsla(32, 85%, 26%, 1);
}

.status-label--sold {
  background: hsla(0, 55%, 92%, 1);
  color: hsla(0, 55%, 34%, 1);
}

@media (prefers-color-scheme: dark) {
  .status-label--on-sale {
    background: hsla(160, 35%, 18%, 1);
    color: hsla(145, 65%, 62%, 1);
  }

  .status-label--reserved {
    background: hsla(45, 45%, 18%, 1);
    color: hsla(48, 88%, 58%, 1);
  }

  .status-label--sold {
    background: hsla(0, 40%, 22%, 1);
    color: hsla(0, 75%, 72%, 1);
  }
}

.btn.sm {
  padding: 0.3rem 0.55rem;
  font-size: 0.78rem;
  flex-shrink: 0;
}

.btn-block {
  width: 100%;
  box-sizing: border-box;
}

.btn.danger {
  border: 1px solid #c0392b;
  background: transparent;
  color: #c0392b;
}

.btn.danger:hover:not(:disabled) {
  background: rgba(192, 57, 43, 0.08);
}

@media (max-width: 720px) {
  .search-actions {
    flex-basis: 100%;
    margin-left: 0;
    justify-content: flex-end;
  }
}
</style>

