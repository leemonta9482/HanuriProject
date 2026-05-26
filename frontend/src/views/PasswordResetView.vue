<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { confirmPasswordReset, getPasswordResetStatus } from '@/api/auth'

const route = useRoute()
const router = useRouter()

const token = computed(() => {
  const t = route.query.token
  return typeof t === 'string' ? t.trim() : ''
})

const checking = ref(true)
const tokenValid = ref(false)
const tokenDetail = ref<string | null>(null)

const password = ref('')
const passwordConfirm = ref('')
const error = ref('')
const loading = ref(false)
const doneMessage = ref('')

async function checkToken() {
  checking.value = true
  tokenValid.value = false
  tokenDetail.value = null
  error.value = ''
  doneMessage.value = ''
  if (!token.value) {
    checking.value = false
    tokenDetail.value = '재설정 링크에 토큰이 없습니다. 이메일에 있는 주소 전체를 사용하거나 비밀번호 찾기를 다시 진행해 주세요.'
    return
  }
  try {
    const st = await getPasswordResetStatus(token.value)
    tokenValid.value = st.valid
    tokenDetail.value = st.detail ?? null
  } catch (e) {
    tokenDetail.value = e instanceof Error ? e.message : '상태를 확인하지 못했습니다.'
    tokenValid.value = false
  } finally {
    checking.value = false
  }
}

onMounted(() => void checkToken())
watch(token, () => void checkToken())

async function onSubmit() {
  error.value = ''
  if (password.value.length < 8) {
    error.value = '새 비밀번호는 8자 이상으로 입력해 주세요.'
    return
  }
  if (password.value !== passwordConfirm.value) {
    error.value = '비밀번호 확인이 일치하지 않습니다.'
    return
  }
  loading.value = true
  try {
    const res = await confirmPasswordReset(token.value, password.value)
    doneMessage.value = res.message
  } catch (e) {
    error.value = e instanceof Error ? e.message : '비밀번호 변경에 실패했습니다.'
  } finally {
    loading.value = false
  }
}

function goLogin() {
  void router.replace({ name: 'login', query: { reset: '1' } })
}
</script>

<template>
  <div class="auth-page">
    <div class="card">
      <h1 class="title">새 비밀번호 설정</h1>
      <div v-if="checking" class="hint" role="status">링크를 확인하는 중…</div>
      <template v-else-if="!doneMessage">
        <div v-if="!tokenValid" class="blocked" role="alert">
          <p class="hint error">{{ tokenDetail }}</p>
          <p class="sub">
            링크는 발송 후 <strong>약 5분</strong>만 유효합니다. 시간이 지났다면 비밀번호 찾기로 다시 요청해 주세요.
          </p>
          <RouterLink class="link-btn" to="/forgot-password">비밀번호 찾기</RouterLink>
        </div>
        <template v-else>
          <p class="intro">아래에 새 비밀번호를 입력해 주세요. 본 페이지는 링크가 유효한 동안만 사용할 수 있습니다.</p>
          <form class="form" @submit.prevent="onSubmit">
            <label class="field">
              <span class="label">새 비밀번호</span>
              <input
                v-model="password"
                type="password"
                name="new_password"
                autocomplete="new-password"
                required
                minlength="8"
                maxlength="128"
                placeholder="8자 이상"
              />
            </label>
            <label class="field">
              <span class="label">새 비밀번호 확인</span>
              <input
                v-model="passwordConfirm"
                type="password"
                name="new_password_confirm"
                autocomplete="new-password"
                required
                minlength="8"
                maxlength="128"
                placeholder="한 번 더 입력"
              />
            </label>
            <p v-if="error" class="hint error" role="alert">{{ error }}</p>
            <button class="submit" type="submit" :disabled="loading">
              {{ loading ? '저장 중…' : '비밀번호 변경' }}
            </button>
          </form>
        </template>
      </template>
      <div v-else class="done" role="status">
        <p class="hint success">{{ doneMessage }}</p>
        <button type="button" class="submit" @click="goLogin">로그인하러 가기</button>
      </div>
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
  min-height: min(70vh, 640px);
}

.card {
  width: 100%;
  max-width: 400px;
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
  margin-bottom: 1rem;
  text-align: center;
}

.intro {
  font-size: 0.875rem;
  line-height: 1.55;
  color: var(--color-text);
  margin: 0 0 1rem;
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

.hint {
  font-size: 0.875rem;
  margin: 0;
}

.hint.error {
  color: #c0392b;
}

.hint.success {
  color: hsl(186, 38%, 30%);
  margin-bottom: 1rem;
}

.blocked .sub {
  font-size: 0.8125rem;
  line-height: 1.5;
  margin: 0.75rem 0 1rem;
  color: var(--color-text);
}

.link-btn {
  display: inline-block;
  font-weight: 600;
  color: var(--color-accent, inherit);
}

.done .submit {
  width: 100%;
  margin-top: 0.5rem;
}

.submit {
  margin-top: 0.25rem;
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
</style>
