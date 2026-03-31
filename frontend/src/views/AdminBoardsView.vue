<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import { fetchAdminBoards } from '@/api/admin'
import type { AdminBoard } from '@/api/types'

const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const pages = ref(0)
const items = ref<AdminBoard[]>([])
const loading = ref(false)
const listError = ref('')

const qBoardId = ref('')
const qTitle = ref('')
const qUserId = ref('')

async function load() {
  listError.value = ''
  loading.value = true
  try {
    const boardIdNum = qBoardId.value.trim() ? Number(qBoardId.value.trim()) : undefined
    const data = await fetchAdminBoards(page.value, pageSize.value, {
      board_id: Number.isFinite(boardIdNum as number) ? (boardIdNum as number) : undefined,
      title: qTitle.value,
      user_id: qUserId.value,
    })
    items.value = data.items
    total.value = data.total
    pages.value = data.pages
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
  qBoardId.value = ''
  qTitle.value = ''
  qUserId.value = ''
  onSearch()
}

function prevPage() {
  if (page.value > 1) page.value -= 1
}

function nextPage() {
  if (pages.value && page.value < pages.value) page.value += 1
}
</script>

<template>
  <div class="admin">
    <nav class="tabs">
      <RouterLink class="tab" to="/admin/users">회원관리</RouterLink>
      <RouterLink class="tab active" to="/admin/boards">게시글관리</RouterLink>
    </nav>

    <header class="head">
      <h1 class="h1">게시글 관리</h1>
      <p class="sub">게시글을 조회하고 검색(게시글번호/제목/작성자)할 수 있습니다.</p>
    </header>

    <div v-if="listError" class="banner err" role="alert">{{ listError }}</div>

    <div class="search">
      <label class="s">
        <span>게시글 번호</span>
        <input v-model="qBoardId" type="text" placeholder="예: 123" @keydown.enter.prevent="onSearch" />
      </label>
      <label class="s">
        <span>게시글 이름</span>
        <input v-model="qTitle" type="text" placeholder="제목 검색" @keydown.enter.prevent="onSearch" />
      </label>
      <label class="s">
        <span>작성자</span>
        <input v-model="qUserId" type="text" placeholder="작성자 아이디" @keydown.enter.prevent="onSearch" />
      </label>
      <div class="s actions">
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
          <select v-model.number="pageSize" @change="onPageSizeChange">
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
        <thead>
          <tr>
            <th>게시글 번호</th>
            <th>게시글 이름</th>
            <th>작성자</th>
            <th>가격</th>
            <th>상태</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="5" class="empty">불러오는 중…</td>
          </tr>
          <tr v-else-if="!items.length">
            <td colspan="5" class="empty">게시글이 없습니다.</td>
          </tr>
          <tr v-for="b in items" :key="b.board_id">
            <td class="mono">{{ b.board_id }}</td>
            <td class="title">{{ b.title }}</td>
            <td class="mono">{{ b.user_id }}</td>
            <td>{{ b.price.toLocaleString() }}</td>
            <td>{{ b.status }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.admin {
  width: 100%;
  max-width: 1200px;
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

.tab.active {
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

.psize select {
  margin-left: 0.35rem;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
}

.search {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr auto;
  gap: 0.75rem;
  align-items: end;
  margin-bottom: 0.75rem;
}

.s {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.8rem;
}

.s input {
  padding: 0.5rem 0.6rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
}

.s.actions {
  display: flex;
  flex-direction: row;
  gap: 0.5rem;
  align-items: center;
}

.table-wrap {
  overflow-x: auto;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  background: var(--color-background-soft);
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.table th,
.table td {
  padding: 0.65rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.table th {
  font-weight: 600;
  background: var(--color-background-mute);
  white-space: nowrap;
}

.mono {
  font-family: ui-monospace, monospace;
  font-size: 0.8rem;
}

.title {
  max-width: 520px;
  word-break: break-word;
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
</style>

