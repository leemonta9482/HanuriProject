<script setup lang="ts">
import { ref } from 'vue'

import { requestPasswordReset } from '@/api/auth'

const userId = ref('')
const email = ref('')
const message = ref('')
const error = ref('')
const loading = ref(false)

async function onSubmit() {
  message.value = ''
  error.value = ''
  loading.value = true
  try {
    const res = await requestPasswordReset(userId.value, email.value)
    message.value = res.message
  } catch (e) {
    error.value = e instanceof Error ? e.message : '요청을 처리하지 못했습니다.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="card">
      <h1 class="title">비밀번호 찾기</h1>
      <p class="intro">
        <strong>아이디</strong>와 가입 시 <strong>이메일</strong>이 계정 정보와 같으면 재설정 메일을 보냅니다.
        발송 후 <strong>5분</strong> 이내에 메일 속 링크로 새 비밀번호를 정해 주세요.
      </p>
      <form v-if="!message" class="form" @submit.prevent="onSubmit">
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
          <span class="label">이메일</span>
          <input
            v-model="email"
            type="email"
            name="email"
            autocomplete="email"
            required
            placeholder="가입 시 사용한 이메일"
          />
        </label>
        <p v-if="error" class="hint error" role="alert">{{ error }}</p>
        <button class="submit" type="submit" :disabled="loading">
          {{ loading ? '처리 중…' : '재설정 메일 보내기' }}
        </button>
      </form>
      <div v-else class="done" role="status">
        <p class="hint success">{{ message }}</p>
        <p class="sub">직접 요청한 적이 없다면 메일 속 링크는 열지 말고 삭제해 주세요.</p>
      </div>
      <p class="footer">
        <RouterLink class="link" to="/login">로그인으로 돌아가기</RouterLink>
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
  margin-bottom: 0.75rem;
  text-align: center;
}

.intro {
  font-size: 0.875rem;
  line-height: 1.55;
  color: var(--color-text);
  margin: 0 0 1.25rem;
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
}

.done .sub {
  font-size: 0.8125rem;
  line-height: 1.5;
  color: var(--color-text-muted, var(--color-text));
  margin: 0.75rem 0 0;
  opacity: 0.92;
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
}

.link {
  font-weight: 600;
}
</style>
