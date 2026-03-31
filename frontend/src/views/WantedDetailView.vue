<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { openChatRoom } from '@/api/chat'
import { deleteWanted, fetchWanted } from '@/api/wanted'
import type { WantedPost } from '@/api/types'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const wantedId = () => Number(route.params.id)

const item = ref<WantedPost | null>(null)
const error = ref('')
const loading = ref(true)
const deleting = ref(false)

function formatPrice(n: number | null): string {
  if (n == null || Number.isNaN(n)) return '미정'
  return new Intl.NumberFormat('ko-KR').format(n) + '원'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    item.value = await fetchWanted(wantedId())
  } catch (e) {
    error.value = e instanceof Error ? e.message : '불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

async function onOpenChat() {
  if (!item.value || item.value.is_owner) return
  try {
    const { room_id } = await openChatRoom({ kind: 'wanted', wanted_id: item.value.wanted_id })
    await router.push({ name: 'chat', query: { room: String(room_id) } })
  } catch (e) {
    error.value = e instanceof Error ? e.message : '채팅방을 열 수 없습니다.'
  }
}

async function remove() {
  if (!item.value?.is_owner) return
  if (!confirm('이 구매 희망글을 삭제할까요?')) return
  deleting.value = true
  error.value = ''
  try {
    await deleteWanted(item.value.wanted_id)
    await router.push({ name: 'home' })
  } catch (e) {
    error.value = e instanceof Error ? e.message : '삭제에 실패했습니다.'
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="page">
    <nav class="crumb">
      <RouterLink to="/">거래 목록</RouterLink>
      <span aria-hidden="true"> / </span>
      <span>구매 희망</span>
    </nav>

    <p v-if="loading" class="hint">불러오는 중…</p>
    <p v-else-if="error" class="err" role="alert">{{ error }}</p>
    <article v-else-if="item" class="card">
      <p class="badge">구매 희망글</p>
      <h1 class="title">{{ item.title }}</h1>
      <p class="meta">{{ item.author_name }} · 희망가 {{ formatPrice(item.max_price) }}</p>
      <p v-if="item.preferred_location" class="loc">희망 장소: {{ item.preferred_location }}</p>
      <p v-if="item.description" class="desc">{{ item.description }}</p>
      <div v-if="auth.isLoggedIn && !item.is_owner" class="chat-row">
        <button type="button" class="btn primary" @click="onOpenChat">구매하기</button>
        <span class="chat-hint">판매를 제안하며 글 작성자와 채팅을 시작합니다.</span>
      </div>
      <div v-if="item.is_owner" class="owner-row">
        <button type="button" class="btn danger" :disabled="deleting" @click="remove">
          {{ deleting ? '삭제 중…' : '삭제' }}
        </button>
      </div>
    </article>
  </div>
</template>

<style scoped>
.page {
  max-width: 640px;
  margin: 0 auto;
  padding: 0 0.5rem 2rem;
}

.crumb {
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.crumb a {
  color: var(--color-heading);
  font-weight: 600;
}

.hint,
.err {
  margin-bottom: 1rem;
}

.err {
  color: #c0392b;
}

.card {
  padding: 1.25rem;
  border-radius: 12px;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
}

.badge {
  display: inline-block;
  margin: 0 0 0.75rem;
  padding: 0.2rem 0.5rem;
  font-size: 0.78rem;
  font-weight: 600;
  border-radius: 6px;
  background: hsla(200, 80%, 40%, 0.15);
  color: hsl(200, 70%, 30%);
}

.title {
  font-size: 1.35rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  line-height: 1.35;
}

.meta {
  font-size: 0.92rem;
  opacity: 0.9;
}

.loc {
  margin-top: 0.75rem;
  font-size: 0.95rem;
}

.desc {
  margin-top: 1rem;
  font-size: 0.95rem;
  line-height: 1.55;
  white-space: pre-wrap;
}

.chat-row {
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.65rem;
}

.chat-hint {
  font-size: 0.85rem;
  color: var(--color-text);
  opacity: 0.88;
  line-height: 1.4;
}

.btn.primary {
  background: hsla(160, 100%, 37%, 1);
  border-color: transparent;
  color: #fff;
}

.btn.primary:hover {
  filter: brightness(1.05);
}

.owner-row {
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
}

.btn {
  padding: 0.45rem 0.85rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
  font-size: 0.9rem;
  cursor: pointer;
}

.btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.btn.danger {
  border-color: #c0392b;
  color: #c0392b;
}
</style>
