<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { fetchPublicSchools, registerUser, verifyStudentId } from '@/api/auth'
import type { PublicSchoolItem } from '@/api/types'

const router = useRouter()

const userId = ref('')
const password = ref('')
const passwordConfirm = ref('')
const name = ref('')
const schoolName = ref('')
const phone = ref('')
const email = ref('')
const studentId = ref('')
const interestMajor = ref('')
const studentIdCard = ref<File | null>(null)

const error = ref('')
const loading = ref(false)
const verificationToken = ref<string | null>(null)
const verifyError = ref('')
const verifyOk = ref(false)
const verifyLoading = ref(false)

const schools = ref<PublicSchoolItem[]>([])
const schoolsLoading = ref(false)
const schoolsError = ref('')

async function loadSchools() {
  schoolsError.value = ''
  schoolsLoading.value = true
  try {
    const res = await fetchPublicSchools()
    schools.value = res.items
  } catch (e) {
    schoolsError.value = e instanceof Error ? e.message : '학교 목록을 불러오지 못했습니다.'
    schools.value = []
  } finally {
    schoolsLoading.value = false
  }
}

onMounted(() => loadSchools())

function onStudentCardChange(ev: Event) {
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0]
  studentIdCard.value = file ?? null
  verificationToken.value = null
  verifyOk.value = false
  verifyError.value = ''
}

function clearVerificationIfIdentityChanged() {
  verificationToken.value = null
  verifyOk.value = false
  verifyError.value = ''
}

async function onVerifyStudentId() {
  verifyError.value = ''
  verifyOk.value = false
  verificationToken.value = null
  const n = name.value.trim()
  const sn = schoolName.value.trim()
  const sid = studentId.value.trim()
  if (!n || !sn) {
    verifyError.value = '이름과 학교명을 입력한 뒤 인증해 주세요.'
    return
  }
  if (!sid) {
    verifyError.value = '학번을 입력한 뒤 인증해 주세요.'
    return
  }
  if (!studentIdCard.value) {
    verifyError.value = '학생증 이미지를 선택해 주세요.'
    return
  }
  verifyLoading.value = true
  try {
    const res = await verifyStudentId({
      name: n,
      school_name: sn,
      student_id: sid,
      student_id_card: studentIdCard.value,
    })
    verificationToken.value = res.verification_token
    verifyOk.value = true
  } catch (e) {
    verifyError.value = e instanceof Error ? e.message : '학생증 인증에 실패했습니다.'
  } finally {
    verifyLoading.value = false
  }
}

async function onSubmit() {
  error.value = ''
  if (password.value !== passwordConfirm.value) {
    error.value = '비밀번호가 일치하지 않습니다.'
    return
  }
  if (password.value.length < 8) {
    error.value = '비밀번호는 8자 이상이어야 합니다.'
    return
  }
  if (!studentIdCard.value) {
    error.value = '학생증 이미지를 첨부해 주세요.'
    return
  }
  if (!studentId.value.trim()) {
    error.value = '학번을 입력해 주세요.'
    return
  }
  if (!verificationToken.value) {
    error.value = '학생증 인증하기를 눌러 이름·학교명·학번이 카드와 일치하는지 확인해 주세요.'
    return
  }
  loading.value = true
  try {
    await registerUser({
      user_id: userId.value.trim(),
      password: password.value,
      name: name.value.trim(),
      school_name: schoolName.value.trim(),
      phone: phone.value.trim(),
      email: email.value.trim(),
      student_id: studentId.value.trim(),
      interest_major: interestMajor.value.trim() || null,
      student_id_card: studentIdCard.value,
      student_id_verification_token: verificationToken.value,
    })
    await router.push({ name: 'login', query: { pending: '1' } })
  } catch (e) {
    error.value = e instanceof Error ? e.message : '회원가입에 실패했습니다.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="card">
      <h1 class="title">회원가입</h1>
      <p class="lead">
        가입 신청 후 관리자 승인이 완료되어야 로그인할 수 있습니다. 학생증 사진으로 이름·학교명·학번을 확인한 뒤 가입할 수
        있으며, 동일 학교의 같은 학번으로는 중복 가입이 불가합니다.
      </p>
      <form class="form" @submit.prevent="onSubmit">
        <label class="field">
          <span class="label">이름 <span class="req">*</span></span>
          <input
            v-model="name"
            type="text"
            name="name"
            required
            maxlength="50"
            placeholder="학생증과 동일하게"
            @input="clearVerificationIfIdentityChanged"
          />
        </label>
        <label class="field">
          <span class="label">학교명 <span class="req">*</span></span>
          <select
            v-model="schoolName"
            name="school_name"
            required
            class="field-select"
            :disabled="schoolsLoading || !!schoolsError"
            @change="clearVerificationIfIdentityChanged"
          >
            <option value="" disabled>
              {{ schoolsLoading ? '학교 목록 불러오는 중…' : '학교를 선택해 주세요' }}
            </option>
            <option v-for="s in schools" :key="s.school_id" :value="s.name">
              {{ s.name }}{{ s.region ? ` (${s.region})` : '' }}
            </option>
          </select>
          <span v-if="schoolsError" class="file-hint" style="color: #c0392b">{{ schoolsError }}</span>
          <span v-else-if="!schoolsLoading && !schools.length" class="file-hint">
            등록된 학교가 없습니다. 관리자에게 문의해 주세요.
          </span>
        </label>
        <label class="field">
          <span class="label">학번 <span class="req">*</span></span>
          <input
            v-model="studentId"
            type="text"
            name="student_id"
            required
            maxlength="20"
            placeholder="학생증에 적힌 학번 그대로"
            @input="clearVerificationIfIdentityChanged"
          />
        </label>
        <label class="field">
          <span class="label">학생증 이미지 <span class="req">*</span></span>
          <input
            type="file"
            name="student_id_card"
            accept="image/jpeg,image/png,image/webp,image/gif"
            required
            class="file-input"
            @change="onStudentCardChange"
          />
          <span class="file-hint">JPEG, PNG, WebP, GIF · 최대 5MB</span>
        </label>
        <div class="verify-row">
          <button
            type="button"
            class="btn-verify"
            :disabled="verifyLoading || loading"
            @click="onVerifyStudentId"
          >
            {{ verifyLoading ? '인증 중…' : '학생증 인증하기' }}
          </button>
        </div>
        <p v-if="verifyOk" class="hint success" role="status">학생증과 이름·학교명·학번이 일치합니다. 아래 정보를 입력한 뒤 가입해 주세요.</p>
        <p v-if="verifyError" class="hint error" role="alert">{{ verifyError }}</p>

        <label class="field">
          <span class="label">아이디 <span class="req">*</span></span>
          <input
            v-model="userId"
            type="text"
            name="user_id"
            autocomplete="username"
            required
            maxlength="50"
            placeholder="로그인에 사용할 아이디"
          />
        </label>
        <label class="field">
          <span class="label">비밀번호 <span class="req">*</span></span>
          <input
            v-model="password"
            type="password"
            name="password"
            autocomplete="new-password"
            required
            minlength="8"
            maxlength="128"
            placeholder="8자 이상"
          />
        </label>
        <label class="field">
          <span class="label">비밀번호 확인 <span class="req">*</span></span>
          <input
            v-model="passwordConfirm"
            type="password"
            name="password_confirm"
            autocomplete="new-password"
            required
            placeholder="비밀번호 다시 입력"
          />
        </label>
        <label class="field">
          <span class="label">전화번호 <span class="req">*</span></span>
          <input
            v-model="phone"
            type="tel"
            name="phone"
            required
            maxlength="20"
            placeholder="010-0000-0000"
          />
        </label>
        <label class="field">
          <span class="label">이메일 <span class="req">*</span></span>
          <input v-model="email" type="email" name="email" required placeholder="email@example.com" />
        </label>
        <label class="field">
          <span class="label">관심 전공</span>
          <input
            v-model="interestMajor"
            type="text"
            name="interest_major"
            maxlength="100"
            placeholder="선택"
          />
        </label>
        <p v-if="error" class="hint error" role="alert">{{ error }}</p>
        <button class="submit" type="submit" :disabled="loading || !verificationToken">
          {{ loading ? '처리 중…' : '가입 신청하기' }}
        </button>
      </form>
      <p class="footer">
        이미 계정이 있으신가요?
        <RouterLink class="link" to="/login">로그인</RouterLink>
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 0;
  min-height: min(80vh, 900px);
}

.card {
  width: 100%;
  max-width: 440px;
  padding: 2rem;
  border-radius: 12px;
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
}

.title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-heading);
  margin-bottom: 0.75rem;
  text-align: center;
}

.lead {
  font-size: 0.875rem;
  line-height: 1.5;
  color: var(--color-text);
  opacity: 0.9;
  margin-bottom: 1.25rem;
  text-align: center;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.label {
  font-size: 0.875rem;
  color: var(--color-text);
}

.req {
  color: hsl(186, 38%, 32%);
}

.field input {
  padding: 0.65rem 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
  font-size: 1rem;
}

.field input:focus {
  outline: 2px solid rgba(92, 176, 185, 0.45);
  outline-offset: 0;
  border-color: rgba(92, 176, 185, 0.6);
}

.field-select {
  padding: 0.65rem 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
  font-size: 1rem;
  appearance: auto;
}

.field-select:focus {
  outline: 2px solid rgba(92, 176, 185, 0.45);
  outline-offset: 0;
  border-color: rgba(92, 176, 185, 0.6);
}

.field-select:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.file-input {
  padding: 0.5rem 0 !important;
  font-size: 0.9rem !important;
}

.file-hint {
  font-size: 0.75rem;
  opacity: 0.8;
}

.hint {
  font-size: 0.875rem;
  margin: 0;
}

.hint.error {
  color: #c0392b;
}

.hint.success {
  color: hsl(160, 45%, 28%);
  font-size: 0.82rem;
}

.verify-row {
  margin: -0.25rem 0 0.35rem;
}

.btn-verify {
  width: 100%;
  padding: 0.65rem 1rem;
  border-radius: 8px;
  border: 1px solid var(--color-accent);
  background: transparent;
  color: hsl(186, 38%, 28%);
  font-weight: 600;
  font-size: 0.92rem;
  cursor: pointer;
  transition:
    background 0.15s,
    color 0.15s;
}

.btn-verify:hover:not(:disabled) {
  background: rgba(92, 176, 185, 0.12);
}

.btn-verify:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.submit {
  margin-top: 0.35rem;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 8px;
  background: var(--color-accent);
  color: #fff;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: filter 0.2s;
}

.submit:hover:not(:disabled) {
  filter: brightness(1.05);
}

.submit:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.footer {
  margin-top: 1.5rem;
  text-align: center;
  font-size: 0.9rem;
  color: var(--color-text);
}

.link {
  font-weight: 600;
  margin-left: 0.25rem;
}
</style>
