<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import { fetchAdminUsers, patchAdminUser } from '@/api/admin'
import { uploadsPublicUrl } from '@/api/client'
import type { AdminUser, AdminUserUpdatePayload } from '@/api/types'

const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const pages = ref(0)
const items = ref<AdminUser[]>([])
const loading = ref(false)
const listError = ref('')

const userSearchBy = ref<'user_id' | 'name' | 'school_name'>('user_id')
const userSearchQuery = ref('')

const userSearchPlaceholder = computed(() => {
  switch (userSearchBy.value) {
    case 'user_id':
      return '아이디를 입력하세요'
    case 'name':
      return '이름을 입력하세요'
    case 'school_name':
      return '학교명을 입력하세요'
    default:
      return ''
  }
})

const modalOpen = ref(false)
const editing = ref<AdminUser | null>(null)
const form = ref<AdminUserUpdatePayload & { name: string; phone: string; email: string }>({
  name: '',
  phone: '',
  email: '',
})
const formStudentId = ref('')
const formInterestMajor = ref('')
const formManner = ref(0)
const formTrust = ref(0)
const formStudentVerified = ref(false)
const formAccountStatus = ref<'ACTIVE' | 'DORMANT' | 'DELETED'>('ACTIVE')
const formRegistrationStatus = ref<'PENDING' | 'APPROVED' | 'REJECTED'>('PENDING')
const formIsAdmin = ref(false)
const saveError = ref('')
const saving = ref(false)

async function load() {
  listError.value = ''
  loading.value = true
  try {
    const q = userSearchQuery.value.trim()
    const filters: { user_id?: string; name?: string; school_name?: string } = {}
    if (q) {
      if (userSearchBy.value === 'user_id') filters.user_id = q
      else if (userSearchBy.value === 'name') filters.name = q
      else filters.school_name = q
    }
    const data = await fetchAdminUsers(page.value, pageSize.value, filters)
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
  userSearchBy.value = 'user_id'
  userSearchQuery.value = ''
  onSearch()
}

function openEdit(u: AdminUser) {
  editing.value = u
  form.value.name = u.name
  form.value.phone = u.phone
  form.value.email = u.email
  formStudentId.value = u.student_id ?? ''
  formInterestMajor.value = u.interest_major ?? ''
  formManner.value = u.manner_score
  formTrust.value = u.trust_score
  formStudentVerified.value = u.student_verified
  formAccountStatus.value = u.account_status as 'ACTIVE' | 'DORMANT' | 'DELETED'
  formRegistrationStatus.value = u.registration_status as 'PENDING' | 'APPROVED' | 'REJECTED'
  formIsAdmin.value = u.is_admin
  saveError.value = ''
  modalOpen.value = true
}

function closeModal() {
  modalOpen.value = false
  editing.value = null
}

async function saveEdit() {
  if (!editing.value) return
  saveError.value = ''
  saving.value = true
  try {
    const payload: AdminUserUpdatePayload = {
      name: form.value.name.trim(),
      phone: form.value.phone.trim(),
      email: form.value.email.trim(),
      student_id: formStudentId.value.trim() || null,
      interest_major: formInterestMajor.value.trim() || null,
      manner_score: formManner.value,
      trust_score: formTrust.value,
      student_verified: formStudentVerified.value,
      account_status: formAccountStatus.value,
      registration_status: formRegistrationStatus.value,
      is_admin: formIsAdmin.value,
    }
    await patchAdminUser(editing.value.user_id, payload)
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

function regLabel(s: string) {
  if (s === 'PENDING') return '승인 대기'
  if (s === 'APPROVED') return '승인됨'
  if (s === 'REJECTED') return '거절'
  return s
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
      <h1 class="h1">회원 관리</h1>
      <p class="sub">전체 회원 정보를 조회하고 승인·학생 인증·계정 상태를 수정할 수 있습니다.</p>
    </header>

    <div v-if="listError" class="banner err" role="alert">{{ listError }}</div>

    <div class="search">
      <label class="s search-combo">
        <span>검색</span>
        <div class="search-row">
          <select v-model="userSearchBy" class="select-theme" aria-label="검색 항목">
            <option value="user_id">아이디</option>
            <option value="name">이름</option>
            <option value="school_name">학교명</option>
          </select>
          <input
            v-model="userSearchQuery"
            type="search"
            class="search-input"
            :placeholder="userSearchPlaceholder"
            maxlength="100"
            autocomplete="off"
            @keydown.enter.prevent="onSearch"
          />
        </div>
      </label>
      <div class="s actions">
        <button type="button" class="btn ghost" :disabled="loading" @click="onReset">초기화</button>
        <button type="button" class="btn primary" :disabled="loading" @click="onSearch">검색</button>
      </div>
    </div>

    <div class="toolbar">
      <span class="meta"
        >총 <strong>{{ total }}</strong
        >명 · 페이지 {{ page }} / {{ pages || 1 }}</span
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
        <thead>
          <tr>
            <th class="num">회원번호</th>
            <th>아이디</th>
            <th>이름</th>
            <th>이메일</th>
            <th>가입 승인</th>
            <th>학생 인증</th>
            <th>계정</th>
            <th>관리자</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="8" class="empty">불러오는 중…</td>
          </tr>
          <tr v-else-if="!items.length">
            <td colspan="8" class="empty">회원이 없습니다.</td>
          </tr>
          <tr v-for="(u, idx) in items" :key="u.user_id">
            <td class="mono num">{{ (page - 1) * pageSize + idx + 1 }}</td>
            <td class="mono">{{ u.user_id }}</td>
            <td>{{ u.name }}</td>
            <td class="email">{{ u.email }}</td>
            <td><span class="pill">{{ regLabel(u.registration_status) }}</span></td>
            <td>{{ u.student_verified ? '학생 인증 완료' : '학생 인증 미완료' }}</td>
            <td>{{ u.account_status }}</td>
            <td>{{ u.is_admin ? '관리자' : '일반유저' }}</td>
            <td>
              <button type="button" class="btn sm" @click="openEdit(u)">수정</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <Teleport to="body">
      <div v-if="modalOpen" class="modal-backdrop" @click.self="closeModal">
        <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
          <h2 id="modal-title" class="modal-title">
            회원 수정 · {{ editing?.user_id }}
          </h2>

          <div v-if="editing" class="modal-body">
            <div class="preview-block">
              <span class="pv-label">학생증 이미지</span>
              <a
                class="img-link"
                :href="uploadsPublicUrl(editing.student_id_card_path)"
                target="_blank"
                rel="noopener noreferrer"
              >
                새 탭에서 크게 보기
              </a>
              <div class="thumb-wrap">
                <img
                  class="thumb"
                  :src="uploadsPublicUrl(editing.student_id_card_path)"
                  alt="학생증"
                />
              </div>
            </div>

            <div class="grid">
              <label class="f"
                >이름 <input v-model="form.name" type="text" maxlength="50"
              /></label>
              <label class="f"
                >전화 <input v-model="form.phone" type="text" maxlength="20"
              /></label>
              <label class="f"
                >이메일 <input v-model="form.email" type="email"
              /></label>
              <label class="f"
                >학번 <input v-model="formStudentId" type="text" maxlength="20"
              /></label>
              <label class="f full"
                >관심 전공
                <input v-model="formInterestMajor" type="text" maxlength="100"
              /></label>
              <label class="f"
                >매너 점수 <input v-model.number="formManner" type="number" step="0.1"
              /></label>
              <label class="f"
                >신뢰 점수 <input v-model.number="formTrust" type="number" step="0.1"
              /></label>
              <label class="f"
                >가입 승인
                <select v-model="formRegistrationStatus" class="select-theme select-theme--block">
                  <option value="PENDING">승인 대기</option>
                  <option value="APPROVED">승인됨</option>
                  <option value="REJECTED">거절</option>
                </select>
              </label>
              <label class="f"
                >계정 상태
                <select v-model="formAccountStatus" class="select-theme select-theme--block">
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="DORMANT">DORMANT</option>
                  <option value="DELETED">DELETED</option>
                </select>
              </label>
              <label class="f chk"
                ><input v-model="formStudentVerified" type="checkbox" /> 학생 인증 완료</label
              >
              <label class="f chk"
                ><input v-model="formIsAdmin" type="checkbox" /> 관리자 권한</label
              >
            </div>

            <p v-if="saveError" class="banner err">{{ saveError }}</p>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn ghost" @click="closeModal">취소</button>
            <button type="button" class="btn primary" :disabled="saving" @click="saveEdit">
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
  box-shadow: 0 0 0 2px hsla(160, 100%, 37%, 0.2);
  border-color: hsla(160, 100%, 37%, 0.45);
}

.s.actions {
  display: flex;
  flex-direction: row;
  gap: 0.5rem;
  align-items: center;
}

.btn.primary {
  background: hsla(160, 100%, 37%, 1);
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

.email {
  word-break: break-all;
  max-width: 220px;
}

.pill {
  display: inline-block;
  padding: 0.15rem 0.45rem;
  border-radius: 12px;
  background: hsla(160, 100%, 37%, 0.12);
  font-size: 0.8rem;
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
  max-width: 520px;
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
  gap: 1rem;
}

.preview-block {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.pv-label {
  font-size: 0.8rem;
  font-weight: 600;
}

.img-link {
  font-size: 0.85rem;
}

.thumb-wrap {
  width: 100%;
  max-height: 200px;
  overflow: hidden;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-background-mute);
}

.thumb {
  width: 100%;
  height: auto;
  display: block;
  object-fit: contain;
  max-height: 200px;
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.f {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.8rem;
}

.f.full {
  grid-column: 1 / -1;
}

.f.chk {
  flex-direction: row;
  align-items: center;
  gap: 0.5rem;
}

.f input {
  padding: 0.45rem 0.5rem;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
  font-size: 0.9rem;
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
