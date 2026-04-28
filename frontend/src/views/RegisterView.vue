<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { fetchPublicSchools, checkUserIdAvailable, registerUser, verifyStudentId, sendRegistrationEmailCode, verifyRegistrationEmailCode } from '@/api/auth'
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

const userIdVerifiedFor = ref<string | null>(null)
const userIdCheckError = ref('')
const userIdCheckLoading = ref(false)

const emailCode = ref('')
const emailChallengeToken = ref<string | null>(null)
const emailCodeRequestFor = ref<string | null>(null)
const emailVerificationToken = ref<string | null>(null)
const emailVerifiedFor = ref<string | null>(null)
const emailSendError = ref('')
const emailVerifyError = ref('')
const emailSendHint = ref('')
const emailSendLoading = ref(false)
const emailVerifyLoading = ref(false)

const userIdLocked = computed(
  () => !!userIdVerifiedFor.value && userId.value.trim() === userIdVerifiedFor.value,
)

const emailLocked = computed(
  () =>
    !!emailVerifiedFor.value && email.value.trim().toLowerCase() === emailVerifiedFor.value,
)

function clearEmailVerification() {
  emailChallengeToken.value = null
  emailCodeRequestFor.value = null
  emailVerificationToken.value = null
  emailVerifiedFor.value = null
  emailCode.value = ''
  emailSendError.value = ''
  emailVerifyError.value = ''
  emailSendHint.value = ''
}

function onEmailInput() {
  const t = email.value.trim().toLowerCase()
  if (emailVerifiedFor.value !== null && t !== emailVerifiedFor.value) {
    clearEmailVerification()
    return
  }
  if (emailCodeRequestFor.value !== null && t !== emailCodeRequestFor.value) {
    emailChallengeToken.value = null
    emailCodeRequestFor.value = null
    emailCode.value = ''
    emailSendError.value = ''
    emailVerifyError.value = ''
    emailSendHint.value = ''
    emailVerificationToken.value = null
    emailVerifiedFor.value = null
  }
}

function onEmailCodeInput() {
  const d = emailCode.value.replace(/\D/g, '').slice(0, 4)
  if (d !== emailCode.value) emailCode.value = d
}

function unlockEmail() {
  clearEmailVerification()
}

async function onSendEmailCode() {
  emailSendError.value = ''
  emailVerifyError.value = ''
  emailSendHint.value = ''
  const addr = email.value.trim()
  if (!addr) {
    emailSendError.value = '이메일을 입력해 주세요.'
    return
  }
  emailSendLoading.value = true
  try {
    const res = await sendRegistrationEmailCode(addr)
    emailChallengeToken.value = res.challenge_token
    emailCodeRequestFor.value = addr.toLowerCase()
    emailVerificationToken.value = null
    emailVerifiedFor.value = null
    emailCode.value = ''
    emailSendHint.value = '인증번호가 메일로 발송되었습니다. 스팸함도 확인해 주세요.'
  } catch (e) {
    emailSendError.value = e instanceof Error ? e.message : '인증번호 발송에 실패했습니다.'
  } finally {
    emailSendLoading.value = false
  }
}

async function onVerifyEmailCode() {
  emailVerifyError.value = ''
  if (!emailChallengeToken.value) {
    emailVerifyError.value = '먼저 인증번호 받기를 눌러 주세요.'
    return
  }
  const digits = emailCode.value.replace(/\D/g, '')
  if (digits.length !== 4) {
    emailVerifyError.value = '인증번호 4자리를 입력해 주세요.'
    return
  }
  emailVerifyLoading.value = true
  try {
    const res = await verifyRegistrationEmailCode(emailChallengeToken.value, digits)
    emailVerificationToken.value = res.email_verification_token
    emailVerifiedFor.value = email.value.trim().toLowerCase()
    emailSendHint.value = ''
  } catch (e) {
    emailVerifyError.value = e instanceof Error ? e.message : '인증에 실패했습니다.'
  } finally {
    emailVerifyLoading.value = false
  }
}

function unlockUserId() {
  userIdVerifiedFor.value = null
  userIdCheckError.value = ''
}

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

function onUserIdInput() {
  const t = userId.value.trim()
  if (userIdVerifiedFor.value !== null && t !== userIdVerifiedFor.value) {
    userIdVerifiedFor.value = null
  }
  userIdCheckError.value = ''
}

async function onCheckUserId() {
  userIdCheckError.value = ''
  const id = userId.value.trim()
  if (!id) {
    userIdCheckError.value = '아이디를 입력해 주세요.'
    userIdVerifiedFor.value = null
    return
  }
  userIdCheckLoading.value = true
  try {
    const res = await checkUserIdAvailable(id)
    if (res.available) {
      userIdVerifiedFor.value = id
      userIdCheckError.value = ''
    } else {
      userIdVerifiedFor.value = null
      userIdCheckError.value = '이미 사용 중인 아이디입니다.'
    }
  } catch (e) {
    userIdVerifiedFor.value = null
    userIdCheckError.value = e instanceof Error ? e.message : '중복 확인에 실패했습니다.'
  } finally {
    userIdCheckLoading.value = false
  }
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
  const uid = userId.value.trim()
  if (!userIdVerifiedFor.value || uid !== userIdVerifiedFor.value) {
    error.value = '아이디 중복 확인을 완료해 주세요.'
    return
  }
  if (
    !emailVerificationToken.value ||
    !emailVerifiedFor.value ||
    email.value.trim().toLowerCase() !== emailVerifiedFor.value
  ) {
    error.value = '이메일 인증을 완료해 주세요.'
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
      email_verification_token: emailVerificationToken.value,
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
        가입 신청 후 관리자 승인이 완료되어야<br>
        로그인할 수 있습니다.
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
          <div class="user-id-row">
            <input
              v-model="userId"
              type="text"
              name="user_id"
              autocomplete="username"
              required
              maxlength="50"
              placeholder="로그인에 사용할 아이디"
              class="user-id-input"
              :readonly="userIdLocked"
              @input="onUserIdInput"
            />
            <button
              type="button"
              class="btn-id-check"
              :disabled="userIdCheckLoading || loading || userIdLocked"
              @click="onCheckUserId"
            >
              {{ userIdCheckLoading ? '확인 중…' : '중복 확인' }}
            </button>
          </div>
          <p v-if="userIdLocked" class="hint success user-id-success" role="status">
            사용 가능한 아이디입니다.
            <button type="button" class="btn-id-change" @click="unlockUserId">다른 아이디로 변경</button>
          </p>
          <p v-if="userIdCheckError" class="hint error" role="alert">{{ userIdCheckError }}</p>
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
          <input
            v-model="email"
            type="email"
            name="email"
            required
            placeholder="email@example.com"
            autocomplete="email"
            class="email-text-input"
            :readonly="emailLocked"
            @input="onEmailInput"
          />
          <div class="email-send-row">
            <button
              type="button"
              class="btn-email-send"
              :disabled="emailSendLoading || loading || emailLocked"
              @click="onSendEmailCode"
            >
              {{ emailSendLoading ? '발송 중…' : '인증번호 받기' }}
            </button>
          </div>
          <p v-if="emailSendHint" class="hint email-hint-ok">{{ emailSendHint }}</p>
          <p v-if="emailSendError" class="hint error" role="alert">{{ emailSendError }}</p>
          <div class="email-code-row">
            <input
              v-model="emailCode"
              type="text"
              name="email_code"
              inputmode="numeric"
              maxlength="4"
              autocomplete="one-time-code"
              placeholder="인증번호 4자리"
              class="email-code-input"
              :disabled="!emailChallengeToken || emailLocked"
              @input="onEmailCodeInput"
            />
            <button
              type="button"
              class="btn-email-verify"
              :disabled="emailVerifyLoading || loading || emailLocked || !emailChallengeToken"
              @click="onVerifyEmailCode"
            >
              {{ emailVerifyLoading ? '확인 중…' : '인증 확인' }}
            </button>
          </div>
          <p v-if="emailLocked" class="hint success user-id-success" role="status">
            이메일 인증이 완료되었습니다.
            <button type="button" class="btn-id-change" @click="unlockEmail">이메일 변경</button>
          </p>
          <p v-if="emailVerifyError" class="hint error" role="alert">{{ emailVerifyError }}</p>
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
        <button
          class="submit"
          type="submit"
          :disabled="
            loading ||
            !verificationToken ||
            !userIdVerifiedFor ||
            userId.trim() !== userIdVerifiedFor ||
            !emailVerificationToken ||
            !emailVerifiedFor ||
            email.trim().toLowerCase() !== emailVerifiedFor
          "
        >
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

.user-id-row {
  display: flex;
  gap: 0.5rem;
  align-items: stretch;
}

.user-id-row .user-id-input {
  flex: 1;
  min-width: 0;
}

.user-id-input:read-only {
  background: rgba(0, 0, 0, 0.04);
  cursor: default;
  color: var(--color-text);
}

.field .email-text-input:read-only {
  background: rgba(0, 0, 0, 0.04);
  cursor: default;
  color: var(--color-text);
}

.user-id-success {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem 0.75rem;
}

.btn-id-change {
  margin: 0;
  padding: 0;
  border: none;
  background: none;
  color: hsl(186, 38%, 32%);
  font: inherit;
  font-size: 0.85rem;
  font-weight: 600;
  text-decoration: underline;
  text-underline-offset: 2px;
  cursor: pointer;
}

.btn-id-change:hover {
  color: hsl(186, 45%, 24%);
}

.btn-id-check {
  flex: 0 0 auto;
  padding: 0.65rem 0.9rem;
  border-radius: 8px;
  border: 1px solid var(--color-accent);
  background: rgba(92, 176, 185, 0.1);
  color: hsl(186, 38%, 28%);
  font-weight: 600;
  font-size: 0.85rem;
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-id-check:hover:not(:disabled) {
  background: rgba(92, 176, 185, 0.18);
}

.btn-id-check:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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

.email-send-row {
  margin-top: 0.45rem;
}

.btn-email-send {
  width: 100%;
  padding: 0.55rem 1rem;
  border-radius: 8px;
  border: 1px solid var(--color-accent);
  background: transparent;
  color: hsl(186, 38%, 28%);
  font-weight: 600;
  font-size: 0.88rem;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-email-send:hover:not(:disabled) {
  background: rgba(92, 176, 185, 0.12);
}

.btn-email-send:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.email-code-row {
  display: flex;
  gap: 0.5rem;
  align-items: stretch;
  margin-top: 0.55rem;
}

.email-code-input {
  flex: 1;
  min-width: 0;
  letter-spacing: 0.15em;
  font-variant-numeric: tabular-nums;
}

.btn-email-verify {
  flex: 0 0 auto;
  padding: 0.65rem 0.9rem;
  border-radius: 8px;
  border: 1px solid var(--color-accent);
  background: rgba(92, 176, 185, 0.1);
  color: hsl(186, 38%, 28%);
  font-weight: 600;
  font-size: 0.85rem;
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-email-verify:hover:not(:disabled) {
  background: rgba(92, 176, 185, 0.18);
}

.btn-email-verify:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.email-hint-ok {
  margin-top: 0.35rem;
  font-size: 0.82rem;
  opacity: 0.9;
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
