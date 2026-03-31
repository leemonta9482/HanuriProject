<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import { fetchAdminReports, patchAdminReport } from '@/api/admin'
import type { AdminReport, AdminReportStatus } from '@/api/types'

const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const pages = ref(0)
const items = ref<AdminReport[]>([])
const loading = ref(false)
const listError = ref('')

const statusFilter = ref<string>('')

const modalOpen = ref(false)
const editing = ref<AdminReport | null>(null)
const formStatus = ref<AdminReportStatus>('PENDING')
const formNote = ref('')
const saveError = ref('')
const saving = ref(false)

const statusLabel: Record<string, string> = {
  PENDING: '미처리',
  REVIEWED: '검토완료',
  DISMISSED: '기각',
  ACTION_TAKEN: '조치완료',
}

async function load() {
  listError.value = ''
  loading.value = true
  try {
    const data = await fetchAdminReports(page.value, pageSize.value, {
      status: statusFilter.value || undefined,
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

function onFilterChange() {
  page.value = 1
  load()
}

function openReview(r: AdminReport) {
  editing.value = r
  formStatus.value = r.status
  formNote.value = r.admin_note ?? ''
  saveError.value = ''
  modalOpen.value = true
}

function closeModal() {
  modalOpen.value = false
  editing.value = null
}

async function saveReview() {
  if (!editing.value) return
  saveError.value = ''
  saving.value = true
  try {
    await patchAdminReport(editing.value.report_id, {
      status: formStatus.value,
      admin_note: formNote.value.trim() || null,
    })
    await load()
    closeModal()
  } catch (e) {
    saveError.value = e instanceof Error ? e.message : '저장에 실패했습니다.'
  } finally {
    saving.value = false
  }
}

function prevPage() {
  if (page.value > 1) page.value -= 1
}

function nextPage() {
  if (pages.value && page.value < pages.value) page.value += 1
}

function truncate(s: string, n: number) {
  if (s.length <= n) return s
  return s.slice(0, n) + '…'
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
      <h1 class="h1">신고 관리</h1>
      <p class="sub">사용자 신고 내역을 조회하고 처리 상태·메모를 남길 수 있습니다.</p>
    </header>

    <div v-if="listError" class="banner err" role="alert">{{ listError }}</div>

    <div class="toolbar-top">
      <label class="filter">
        <span>처리 상태</span>
        <select v-model="statusFilter" class="select" @change="onFilterChange">
          <option value="">전체</option>
          <option value="PENDING">미처리</option>
          <option value="REVIEWED">검토완료</option>
          <option value="DISMISSED">기각</option>
          <option value="ACTION_TAKEN">조치완료</option>
        </select>
      </label>
    </div>

    <div class="toolbar">
      <span class="meta"
        >총 <strong>{{ total }}</strong
        >건 · 페이지 {{ page }} / {{ pages || 1 }}</span
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
            <th>신고번호</th>
            <th>게시글</th>
            <th>판매자</th>
            <th>신고자</th>
            <th>사유</th>
            <th>상태</th>
            <th>신고일</th>
            <th>관리</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="8" class="empty">불러오는 중…</td>
          </tr>
          <tr v-else-if="!items.length">
            <td colspan="8" class="empty">신고 내역이 없습니다.</td>
          </tr>
          <tr v-for="r in items" :key="r.report_id">
            <td class="mono">{{ r.report_id }}</td>
            <td>
              <span class="title">{{ r.board_title }}</span>
              <span class="subid">#{{ r.board_id }}</span>
            </td>
            <td class="mono">{{ r.seller_id }}</td>
            <td>{{ r.reporter_name }} <span class="subid">({{ r.reporter_id }})</span></td>
            <td class="reason">{{ truncate(r.reason, 80) }}</td>
            <td>
              <span class="badge" :class="'st-' + r.status">{{ statusLabel[r.status] ?? r.status }}</span>
            </td>
            <td class="date">{{ r.created_at ? String(r.created_at).slice(0, 16) : '—' }}</td>
            <td>
              <div class="cell-actions">
                <RouterLink class="link" :to="`/boards/${r.board_id}`" target="_blank">게시글</RouterLink>
                <button type="button" class="btn primary sm" @click="openReview(r)">검토</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <Teleport to="body">
      <div v-if="modalOpen" class="modal-backdrop" @click.self="closeModal">
        <div class="modal" role="dialog" aria-modal="true" aria-labelledby="report-modal-title">
          <h2 id="report-modal-title" class="modal-title">신고 검토 #{{ editing?.report_id }}</h2>
          <p v-if="editing" class="modal-meta">
            게시글: {{ editing.board_title }} (#{{ editing.board_id }}) · 판매자: {{ editing.seller_id }}
          </p>
          <div v-if="editing" class="modal-section">
            <span class="lbl">신고 사유</span>
            <p class="reason-full">{{ editing.reason }}</p>
          </div>
          <label class="modal-field">
            <span>처리 상태</span>
            <select v-model="formStatus" class="select full">
              <option value="PENDING">미처리</option>
              <option value="REVIEWED">검토완료</option>
              <option value="DISMISSED">기각</option>
              <option value="ACTION_TAKEN">조치완료</option>
            </select>
          </label>
          <label class="modal-field">
            <span>관리자 메모</span>
            <textarea v-model="formNote" rows="4" maxlength="2000" placeholder="내부 메모 (선택)" />
          </label>
          <p v-if="saveError" class="modal-err">{{ saveError }}</p>
          <div class="modal-actions">
            <button type="button" class="btn ghost" :disabled="saving" @click="closeModal">닫기</button>
            <button type="button" class="btn primary" :disabled="saving" @click="saveReview">
              {{ saving ? '저장 중…' : '저장' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
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
  flex-wrap: wrap;
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
  text-decoration: none;
}

.tab.router-link-active {
  background: hsla(160, 100%, 37%, 0.12);
  border-color: hsla(160, 100%, 37%, 0.35);
  font-weight: 600;
}

.head {
  margin-bottom: 1rem;
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

.toolbar-top {
  margin-bottom: 0.75rem;
}

.filter {
  display: inline-flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.8rem;
}

.select {
  padding: 0.45rem 0.6rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
  font-size: 0.9rem;
}

.select.full {
  width: 100%;
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

.table-wrap {
  overflow-x: auto;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  background: var(--color-background-soft);
}

.table {
  width: 100%;
  min-width: 900px;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.table th,
.table td {
  padding: 0.65rem 0.75rem;
  text-align: left;
  vertical-align: middle;
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
  font-weight: 500;
  display: block;
}

.subid {
  font-size: 0.78rem;
  opacity: 0.75;
}

.reason {
  max-width: 280px;
  font-size: 0.82rem;
  line-height: 1.4;
  word-break: break-word;
}

.date {
  font-size: 0.82rem;
  white-space: nowrap;
}

.badge {
  display: inline-block;
  padding: 0.2rem 0.45rem;
  border-radius: 6px;
  font-size: 0.78rem;
  font-weight: 600;
}

.st-PENDING {
  background: rgba(241, 196, 15, 0.2);
  color: #b7950b;
}

.st-REVIEWED {
  background: rgba(52, 152, 219, 0.15);
  color: #2874a6;
}

.st-DISMISSED {
  background: rgba(149, 165, 166, 0.25);
  color: #566573;
}

.st-ACTION_TAKEN {
  background: rgba(39, 174, 96, 0.15);
  color: #1e8449;
}

.cell-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  align-items: center;
}

.link {
  font-size: 0.82rem;
  font-weight: 600;
  color: hsla(160, 100%, 30%, 1);
  text-decoration: none;
}

.link:hover {
  text-decoration: underline;
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

.btn.sm {
  padding: 0.3rem 0.55rem;
  font-size: 0.78rem;
}

.btn:disabled {
  opacity: 0.55;
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

.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.modal {
  width: 100%;
  max-width: 520px;
  max-height: 90vh;
  overflow: auto;
  padding: 1.25rem 1.5rem;
  border-radius: 12px;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.2);
}

.modal-title {
  font-size: 1.15rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  color: var(--color-heading);
}

.modal-meta {
  font-size: 0.85rem;
  opacity: 0.9;
  margin-bottom: 1rem;
}

.modal-section {
  margin-bottom: 1rem;
}

.lbl {
  font-size: 0.8rem;
  font-weight: 600;
  display: block;
  margin-bottom: 0.35rem;
}

.reason-full {
  font-size: 0.9rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  padding: 0.65rem 0.75rem;
  border-radius: 8px;
  background: var(--color-background-mute);
  border: 1px solid var(--color-border);
}

.modal-field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin-bottom: 1rem;
  font-size: 0.88rem;
}

.modal-field textarea {
  padding: 0.5rem 0.6rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
  resize: vertical;
  font-family: inherit;
}

.modal-err {
  color: #c0392b;
  font-size: 0.88rem;
  margin-bottom: 0.75rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 0.5rem;
}
</style>
