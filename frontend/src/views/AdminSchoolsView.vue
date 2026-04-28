<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import {
  createAdminSchool,
  deleteAdminSchool,
  fetchAdminSchools,
  patchAdminSchool,
} from '@/api/admin'
import type { AdminSchoolUpdatePayload, School } from '@/api/types'

const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const pages = ref(0)
const items = ref<School[]>([])
const loading = ref(false)
const listError = ref('')

const searchBy = ref<'name' | 'region'>('name')
const searchQuery = ref('')

const searchPlaceholder = computed(() => {
  switch (searchBy.value) {
    case 'name':
      return '학교명을 입력하세요'
    case 'region':
      return '지역을 입력하세요'
    default:
      return ''
  }
})

const modalOpen = ref(false)
const modalMode = ref<'create' | 'edit'>('create')
const editing = ref<School | null>(null)
const formName = ref('')
const formRegion = ref('')
const formActive = ref(true)
const saveError = ref('')
const saving = ref(false)
const removingId = ref<number | null>(null)

async function load() {
  listError.value = ''
  loading.value = true
  try {
    const q = searchQuery.value.trim()
    const filters: { name?: string; region?: string } = {}
    if (q) {
      if (searchBy.value === 'name') filters.name = q
      else filters.region = q
    }
    const data = await fetchAdminSchools(page.value, pageSize.value, filters)
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
  searchBy.value = 'name'
  searchQuery.value = ''
  onSearch()
}

function openCreate() {
  modalMode.value = 'create'
  editing.value = null
  formName.value = ''
  formRegion.value = ''
  formActive.value = true
  saveError.value = ''
  modalOpen.value = true
}

function openEdit(s: School) {
  modalMode.value = 'edit'
  editing.value = s
  formName.value = s.name
  formRegion.value = s.region ?? ''
  formActive.value = s.is_active
  saveError.value = ''
  modalOpen.value = true
}

function closeModal() {
  modalOpen.value = false
  editing.value = null
}

async function saveModal() {
  saveError.value = ''
  const name = formName.value.trim()
  if (!name) {
    saveError.value = '학교명을 입력해 주세요.'
    return
  }
  saving.value = true
  try {
    if (modalMode.value === 'create') {
      await createAdminSchool({
        name,
        region: formRegion.value.trim() || null,
        is_active: formActive.value,
      })
    } else if (editing.value) {
      const payload: AdminSchoolUpdatePayload = {
        name,
        region: formRegion.value.trim() || null,
        is_active: formActive.value,
      }
      await patchAdminSchool(editing.value.school_id, payload)
    }
    await load()
    closeModal()
  } catch (e) {
    saveError.value = e instanceof Error ? e.message : '저장에 실패했습니다.'
  } finally {
    saving.value = false
  }
}

async function removeSchool(s: School) {
  if (!confirm(`「${s.name}」을(를) 삭제할까요?\n해당 학교에 소속된 회원이 있으면 삭제할 수 없습니다.`)) {
    return
  }
  removingId.value = s.school_id
  listError.value = ''
  try {
    await deleteAdminSchool(s.school_id)
    await load()
  } catch (e) {
    listError.value = e instanceof Error ? e.message : '삭제에 실패했습니다.'
  } finally {
    removingId.value = null
  }
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
      <RouterLink class="tab" to="/admin/boards">게시글관리</RouterLink>
      <RouterLink class="tab" to="/admin/reports">신고관리</RouterLink>
      <RouterLink class="tab" to="/admin/schools">가입관리</RouterLink>
    </nav>

    <header class="head">
      <h1 class="h1">가입관리 · 학교 정보</h1>
      <p class="sub">
        회원가입 시 셀렉트로 노출되는 학교 목록을 등록·수정·삭제합니다. <br />
        비활성화(노출 OFF) 시 가입 화면 셀렉트에서 숨겨지며, 학교명 변경 시 기존 회원 정보의 학교명도 함께 갱신됩니다.
      </p>
    </header>

    <div v-if="listError" class="banner err" role="alert">{{ listError }}</div>

    <div class="search">
      <label class="s search-combo">
        <span>검색</span>
        <div class="search-row">
          <select v-model="searchBy" class="select-theme" aria-label="검색 항목">
            <option value="name">학교명</option>
            <option value="region">지역</option>
          </select>
          <input
            v-model="searchQuery"
            type="search"
            class="search-input"
            :placeholder="searchPlaceholder"
            maxlength="100"
            autocomplete="off"
            @keydown.enter.prevent="onSearch"
          />
        </div>
      </label>
      <div class="s actions">
        <button type="button" class="btn ghost" :disabled="loading" @click="onReset">초기화</button>
        <button type="button" class="btn primary" :disabled="loading" @click="onSearch">검색</button>
        <button type="button" class="btn primary" :disabled="loading" @click="openCreate">+ 학교 등록</button>
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
          <select
            v-model.number="pageSize"
            class="select-theme select-theme--compact"
            @change="onPageSizeChange"
          >
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
            <th class="num">번호</th>
            <th>학교명</th>
            <th>지역</th>
            <th>가입 화면 노출</th>
            <th>등록일</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="6" class="empty">불러오는 중…</td>
          </tr>
          <tr v-else-if="!items.length">
            <td colspan="6" class="empty">등록된 학교가 없습니다.</td>
          </tr>
          <tr v-for="(s, idx) in items" :key="s.school_id">
            <td class="mono num">{{ (page - 1) * pageSize + idx + 1 }}</td>
            <td>{{ s.name }}</td>
            <td>{{ s.region || '-' }}</td>
            <td>
              <span class="pill" :class="{ pill_off: !s.is_active }">
                {{ s.is_active ? '노출' : '숨김' }}
              </span>
            </td>
            <td class="mono">{{ s.created_at?.slice?.(0, 10) ?? '-' }}</td>
            <td class="actions-cell">
              <button type="button" class="btn sm" @click="openEdit(s)">수정</button>
              <button
                type="button"
                class="btn sm danger"
                :disabled="removingId === s.school_id"
                @click="removeSchool(s)"
              >
                {{ removingId === s.school_id ? '삭제 중…' : '삭제' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <Teleport to="body">
      <div v-if="modalOpen" class="modal-backdrop" @click.self="closeModal">
        <div class="modal" role="dialog" aria-modal="true" aria-labelledby="school-modal-title">
          <h2 id="school-modal-title" class="modal-title">
            {{ modalMode === 'create' ? '학교 등록' : `학교 수정 · ${editing?.name}` }}
          </h2>

          <div class="modal-body">
            <label class="f full"
              >학교명 <span class="req">*</span>
              <input v-model="formName" type="text" maxlength="100" placeholder="예: 한우리대학교" />
            </label>
            <label class="f full"
              >지역
              <input v-model="formRegion" type="text" maxlength="100" placeholder="예: 서울특별시 (선택)" />
            </label>
            <label class="f chk">
              <input v-model="formActive" type="checkbox" />
              가입 화면 셀렉트에 노출
            </label>

            <p v-if="saveError" class="banner err">{{ saveError }}</p>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn ghost" @click="closeModal">취소</button>
            <button type="button" class="btn primary" :disabled="saving" @click="saveModal">
              {{ saving ? '저장 중…' : modalMode === 'create' ? '등록' : '저장' }}
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
  max-width: 1400px;
  margin: 0 auto;
}

.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
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
  background: rgba(92, 176, 185, 0.12);
  border-color: rgba(92, 176, 185, 0.35);
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
  line-height: 1.5;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.search {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.search-combo {
  flex: 1 1 18rem;
  min-width: 0;
}

.s {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
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
}

.search-input:focus,
.search-row select:focus {
  outline: none;
}

.search-row:focus-within {
  box-shadow: 0 0 0 2px rgba(92, 176, 185, 0.2);
  border-color: rgba(92, 176, 185, 0.45);
}

.s.actions {
  display: flex;
  flex-direction: row;
  gap: 0.5rem;
  align-items: center;
}

.btn.primary {
  background: var(--color-accent);
  color: #fff;
  font-weight: 600;
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

.num {
  width: 92px;
  white-space: nowrap;
}

.pill {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 12px;
  background: rgba(92, 176, 185, 0.15);
  color: hsl(186, 38%, 28%);
  font-size: 0.8rem;
  font-weight: 600;
}

.pill_off {
  background: rgba(120, 120, 120, 0.18);
  color: #555;
}

.actions-cell {
  display: flex;
  gap: 0.4rem;
  white-space: nowrap;
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

.btn.sm {
  padding: 0.3rem 0.6rem;
  font-size: 0.8rem;
}

.btn.primary {
  background: var(--color-accent);
  color: #fff;
  font-weight: 600;
}

.btn.ghost {
  background: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-text);
}

.btn.danger {
  background: rgba(192, 57, 43, 0.12);
  color: #a93226;
  border: 1px solid rgba(192, 57, 43, 0.35);
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

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal {
  width: 100%;
  max-width: 460px;
  max-height: 90vh;
  overflow: auto;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 1.25rem;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.2);
}

.modal-title {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 1rem;
  color: var(--color-heading);
}

.modal-body {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.f {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.85rem;
}

.f.full {
  width: 100%;
}

.f.chk {
  flex-direction: row;
  align-items: center;
  gap: 0.5rem;
}

.f input[type='text'] {
  padding: 0.5rem 0.6rem;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
  font-size: 0.95rem;
}

.req {
  color: hsl(186, 38%, 32%);
  margin-left: 0.15rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1.25rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--color-border);
}
</style>
