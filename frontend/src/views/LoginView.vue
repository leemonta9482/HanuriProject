<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const userId = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

onMounted(() => {
  if (route.query.registered === '1' || route.query.pending === '1') {
    error.value = ''
  }
})

function doLogoutOnly() {
  auth.logout()
  error.value = ''
}

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    // 다른 탭·이전 세션으로 이미 로그인된 경우 기존 토큰을 먼저 제거해야 새 로그인이 정상 동작합니다.
    auth.logout()
    await auth.login(userId.value.trim(), password.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '로그인에 실패했습니다.'
  } finally {
    // router.replace를 await하면 네비게이션이 끝나지 않는 경우 finally가 실행되지 않아 '처리 중'이 멈춥니다.
    loading.value = false
  }
  if (error.value) return
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : ''
  const isLoginRedirect = redirect.startsWith('/login')
  if (redirect && !isLoginRedirect) {
    void router.replace(redirect)
  } else if (auth.isAdmin) {
    void router.replace({ name: 'admin-users' })
  } else {
    void router.replace({ name: 'home' })
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="card">
      <h1 class="title">로그인</h1>
      <div v-if="auth.isLoggedIn" class="already-session" role="status">
        <p class="already-text">다른 계정으로 로그인하려면 먼저 로그아웃해 주세요.</p>
        <button type="button" class="btn-logout" @click="doLogoutOnly">로그아웃</button>
      </div>
      <p v-if="route.query.pending === '1'" class="hint success">
        가입 신청이 접수되었습니다. 관리자 승인 후 로그인할 수 있습니다.
      </p>
      <p v-else-if="route.query.registered === '1'" class="hint success">
        회원가입이 완료되었습니다. 로그인해 주세요.
      </p>
      <form class="form" @submit.prevent="onSubmit">
        <label class="field">
          <span class="label">아이디</span>
          <input
            v-model="userId"
            type="text"
            name="user_id"
            autocomplete="username"
            required
            maxlength="50"
            placeholder="아이디"
          />
        </label>
        <label class="field">
          <span class="label">비밀번호</span>
          <input
            v-model="password"
            type="password"
            name="password"
            autocomplete="current-password"
            required
            placeholder="비밀번호"
          />
        </label>
        <p v-if="error" class="hint error" role="alert">{{ error }}</p>
        <button class="submit" type="submit" :disabled="loading">
          {{ loading ? '처리 중…' : '로그인' }}
        </button>
      </form>
      <p class="footer">
        계정이 없으신가요?
        <RouterLink class="link" to="/register">회원가입</RouterLink>
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
  margin-bottom: 1.25rem;
  text-align: center;
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
  margin-bottom: 0.5rem;
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

.already-session {
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-background-mute);
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  align-items: stretch;
}

.already-text {
  font-size: 0.88rem;
  line-height: 1.45;
  margin: 0;
  color: var(--color-text);
}

.btn-logout {
  padding: 0.45rem 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-logout:hover {
  border-color: var(--color-border-hover);
}
</style>
