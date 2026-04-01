<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { changePassword, fetchUserProfile, updateUserProfile } from '@/api/auth'
import { uploadsPublicUrl } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const loading = ref(true)
const savingProfile = ref(false)
const savingPassword = ref(false)
const error = ref('')
const profileError = ref('')
const passwordError = ref('')
const passwordOk = ref('')

const schoolName = ref('')
const phone = ref('')
const interestMajor = ref('')
const profileImagePath = ref<string | null>(null)
const profileFile = ref<File | null>(null)
const profilePreviewUrl = ref<string | null>(null)
const removeProfileImage = ref(false)
const profileFileInput = ref<HTMLInputElement | null>(null)

const currentPassword = ref('')
const newPassword = ref('')
const newPasswordConfirm = ref('')

function profileImageUrl(path: string | null): string | null {
  if (!path) return null
  return uploadsPublicUrl(path)
}

const displayPreview = computed(() => {
  if (profilePreviewUrl.value) return profilePreviewUrl.value
  if (removeProfileImage.value) return null
  return profileImageUrl(profileImagePath.value)
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    const p = await fetchUserProfile()
    schoolName.value = p.school_name
    phone.value = p.phone
    interestMajor.value = p.interest_major ?? ''
    profileImagePath.value = p.profile_image_path
    profileFile.value = null
    removeProfileImage.value = false
    if (profilePreviewUrl.value) {
      URL.revokeObjectURL(profilePreviewUrl.value)
      profilePreviewUrl.value = null
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '프로필을 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
}

onMounted(() => load())

watch(profileFile, (f) => {
  if (profilePreviewUrl.value) {
    URL.revokeObjectURL(profilePreviewUrl.value)
    profilePreviewUrl.value = null
  }
  if (f) {
    profilePreviewUrl.value = URL.createObjectURL(f)
    removeProfileImage.value = false
  }
})

function onProfileFileChange(ev: Event) {
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0]
  profileFile.value = file ?? null
}

function clearFileInput() {
  profileFile.value = null
  if (profileFileInput.value) profileFileInput.value.value = ''
}

async function saveProfile() {
  profileError.value = ''
  savingProfile.value = true
  try {
    const updated = await updateUserProfile({
      phone: phone.value,
      interest_major: interestMajor.value.trim() || null,
      profile_image: profileFile.value ?? undefined,
      clear_profile_image: removeProfileImage.value && !profileFile.value,
    })
    profileImagePath.value = updated.profile_image_path
    profileFile.value = null
    removeProfileImage.value = false
    if (profilePreviewUrl.value) {
      URL.revokeObjectURL(profilePreviewUrl.value)
      profilePreviewUrl.value = null
    }
    await auth.hydrateFromServer()
  } catch (e) {
    profileError.value = e instanceof Error ? e.message : '저장에 실패했습니다.'
  } finally {
    savingProfile.value = false
  }
}

async function savePassword() {
  passwordError.value = ''
  passwordOk.value = ''
  if (newPassword.value !== newPasswordConfirm.value) {
    passwordError.value = '새 비밀번호가 서로 일치하지 않습니다.'
    return
  }
  if (newPassword.value.length < 8) {
    passwordError.value = '새 비밀번호는 8자 이상이어야 합니다.'
    return
  }
  savingPassword.value = true
  try {
    await changePassword(currentPassword.value, newPassword.value)
    passwordOk.value = '비밀번호가 변경되었습니다.'
    currentPassword.value = ''
    newPassword.value = ''
    newPasswordConfirm.value = ''
  } catch (e) {
    passwordError.value = e instanceof Error ? e.message : '비밀번호 변경에 실패했습니다.'
  } finally {
    savingPassword.value = false
  }
}
</script>

<template>
  <div class="profile-page">
    <div class="wrap">
      <header class="page-head">
        <h1 class="title">프로필 수정</h1>
        <p class="lead">연락처·학과·프로필 사진을 수정할 수 있습니다. 비밀번호는 현재 비밀번호 확인 후 변경됩니다.</p>
      </header>

      <p v-if="loading" class="status">불러오는 중…</p>
      <p v-else-if="error" class="status err">{{ error }}</p>

      <template v-else>
        <section class="card" aria-labelledby="sec-profile">
          <h2 id="sec-profile" class="card-title">개인정보</h2>
          <form class="form" @submit.prevent="saveProfile">
            <label class="field">
              <span class="label">학교명</span>
              <input :value="schoolName" type="text" readonly class="readonly" tabindex="-1" />
            </label>
            <label class="field">
              <span class="label">연락처 <span class="req">*</span></span>
              <input
                v-model="phone"
                type="tel"
                name="phone"
                required
                maxlength="20"
                autocomplete="tel"
                placeholder="휴대폰 번호"
              />
            </label>
            <label class="field">
              <span class="label">학과</span>
              <input
                v-model="interestMajor"
                type="text"
                name="interest_major"
                maxlength="100"
                placeholder="학과(선택)"
              />
            </label>

            <div class="field field--avatar">
              <span class="label">프로필 이미지 <span class="optional">(선택)</span></span>
              <div class="avatar-row">
                <div class="avatar-preview" :class="{ empty: !displayPreview }">
                  <img v-if="displayPreview" :src="displayPreview" alt="" />
                  <span v-else class="ph">이미지 없음</span>
                </div>
                <div class="avatar-actions">
                  <label class="btn-file">
                    사진 선택
                    <input
                      ref="profileFileInput"
                      type="file"
                      accept="image/jpeg,image/png,image/webp,image/gif"
                      @change="onProfileFileChange"
                    />
                  </label>
                  <button
                    v-if="profileFile"
                    type="button"
                    class="btn-text"
                    @click="clearFileInput"
                  >
                    선택 취소
                  </button>
                  <label v-if="profileImagePath && !profileFile" class="check-remove">
                    <input v-model="removeProfileImage" type="checkbox" />
                    프로필 사진 삭제
                  </label>
                </div>
              </div>
            </div>

            <p v-if="profileError" class="hint err">{{ profileError }}</p>
            <button type="submit" class="submit" :disabled="savingProfile">
              {{ savingProfile ? '저장 중…' : '개인정보 저장' }}
            </button>
          </form>
        </section>

        <section class="card" aria-labelledby="sec-password">
          <h2 id="sec-password" class="card-title">비밀번호 변경</h2>
          <form class="form" @submit.prevent="savePassword">
            <label class="field">
              <span class="label">현재 비밀번호 <span class="req">*</span></span>
              <input
                v-model="currentPassword"
                type="password"
                name="current_password"
                autocomplete="current-password"
                maxlength="128"
              />
            </label>
            <label class="field">
              <span class="label">새 비밀번호 <span class="req">*</span></span>
              <input
                v-model="newPassword"
                type="password"
                name="new_password"
                autocomplete="new-password"
                minlength="8"
                maxlength="128"
                placeholder="8자 이상"
              />
            </label>
            <label class="field">
              <span class="label">새 비밀번호 확인 <span class="req">*</span></span>
              <input
                v-model="newPasswordConfirm"
                type="password"
                name="new_password_confirm"
                autocomplete="new-password"
                placeholder="한 번 더 입력"
              />
            </label>
            <p v-if="passwordError" class="hint err">{{ passwordError }}</p>
            <p v-if="passwordOk" class="hint ok">{{ passwordOk }}</p>
            <button type="submit" class="submit secondary" :disabled="savingPassword">
              {{ savingPassword ? '변경 중…' : '비밀번호 변경' }}
            </button>
          </form>
        </section>
      </template>
    </div>
  </div>
</template>

<style scoped>
.profile-page {
  flex: 1;
  width: 100%;
  padding: 1rem 0.5rem 2.5rem;
  box-sizing: border-box;
}

.wrap {
  width: 100%;
  max-width: 560px;
  margin: 0 auto;
}

.page-head {
  margin-bottom: 1.5rem;
}

.title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-heading);
  margin: 0 0 0.5rem;
}

.lead {
  margin: 0;
  font-size: 0.92rem;
  line-height: 1.5;
  color: var(--color-text);
  opacity: 0.9;
}

.status {
  text-align: center;
  padding: 2rem;
  color: var(--color-text);
}

.status.err {
  color: #a93226;
}

.card {
  padding: 1.35rem 1.25rem;
  border-radius: 12px;
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  margin-bottom: 1.25rem;
}

.card-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-heading);
  margin: 0 0 1rem;
  padding-bottom: 0.65rem;
  border-bottom: 1px solid var(--color-border);
}

.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
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
  color: #a93226;
  font-weight: 600;
}

.optional {
  font-weight: 400;
  opacity: 0.75;
  font-size: 0.82rem;
}

.field input:not(.readonly) {
  padding: 0.65rem 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
  font-size: 1rem;
  width: 100%;
  box-sizing: border-box;
}

.field input:focus {
  outline: 2px solid hsla(160, 100%, 37%, 0.45);
  outline-offset: 0;
  border-color: hsla(160, 100%, 37%, 0.6);
}

.field input.readonly {
  width: 100%;
  box-sizing: border-box;
  padding: 0.65rem 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-background-mute);
  color: var(--color-text);
  font-size: 1rem;
  line-height: 1.45;
  cursor: not-allowed;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.field input.readonly:focus {
  outline: none;
  border-color: var(--color-border-hover);
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.06);
}

.field--avatar .avatar-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 1rem;
}

.avatar-preview {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  overflow: hidden;
  border: 1px solid var(--color-border);
  background: var(--color-background-mute);
  flex-shrink: 0;
}

.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-preview.empty .ph {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  font-size: 0.75rem;
  color: var(--color-text);
  opacity: 0.55;
  padding: 0.35rem;
  text-align: center;
}

.avatar-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.5rem;
  min-width: 0;
  flex: 1;
}

.btn-file {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem 0.9rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-file input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  overflow: hidden;
}

.btn-text {
  padding: 0;
  border: none;
  background: none;
  color: hsla(160, 100%, 32%, 1);
  font-size: 0.88rem;
  cursor: pointer;
  text-decoration: underline;
}

.check-remove {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.9rem;
  border-radius: 8px;
  border: 1px solid hsla(0, 45%, 48%, 0.45);
  background: hsla(0, 28%, 97%, 0.85);
  color: var(--color-heading);
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  user-select: none;
  transition:
    border-color 0.15s,
    background 0.15s,
    box-shadow 0.15s;
}

.check-remove:hover {
  border-color: #c0392b;
  background: hsla(0, 40%, 94%, 1);
}

.check-remove:has(input:checked) {
  border-color: #c0392b;
  background: hsla(0, 42%, 92%, 1);
  box-shadow: inset 0 0 0 1px hsla(0, 55%, 45%, 0.12);
}

.check-remove input[type='checkbox'] {
  width: 1.05rem;
  height: 1.05rem;
  margin: 0;
  flex-shrink: 0;
  accent-color: #c0392b;
  cursor: pointer;
}

@media (prefers-color-scheme: dark) {
  .check-remove {
    background: hsla(0, 22%, 16%, 0.9);
    border-color: hsla(0, 35%, 42%, 0.65);
    color: var(--color-text);
  }

  .check-remove:hover {
    background: hsla(0, 28%, 20%, 1);
    border-color: hsla(0, 45%, 48%, 0.85);
  }

  .check-remove:has(input:checked) {
    background: hsla(0, 32%, 18%, 1);
    box-shadow: inset 0 0 0 1px hsla(0, 50%, 42%, 0.35);
  }
}

.hint {
  font-size: 0.875rem;
  margin: 0;
}

.hint.err {
  color: #c0392b;
}

.hint.ok {
  color: hsla(160, 100%, 30%, 1);
}

.submit {
  margin-top: 0.25rem;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 8px;
  background: hsla(160, 100%, 37%, 1);
  color: #fff;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: filter 0.2s;
}

.submit.secondary {
  background: var(--color-background);
  color: var(--color-heading);
  border: 1px solid var(--color-border);
}

.submit:hover:not(:disabled) {
  filter: brightness(1.05);
}

.submit:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

@media (min-width: 480px) {
  .wrap {
    padding: 0 0.25rem;
  }

  .card {
    padding: 1.5rem 1.5rem;
  }
}
</style>
