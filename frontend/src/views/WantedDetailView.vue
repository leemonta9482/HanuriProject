<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { openChatRoom } from '@/api/chat'
import { deleteWanted, fetchWanted } from '@/api/wanted'
import type { WantedPost } from '@/api/types'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const id = computed(() => Number(route.params.id))

const item = ref<WantedPost | null>(null)
const error = ref('')
const loading = ref(false)
const deleting = ref(false)

function formatMaxPrice(n: number | null): string {
  if (n == null || Number.isNaN(n)) return '희망가 미정'
  return new Intl.NumberFormat('ko-KR').format(n) + '원 이하'
}

async function load() {
  if (!auth.isLoggedIn) {
    item.value = null
    error.value = ''
    loading.value = false
    return
  }
  error.value = ''
  loading.value = true
  try {
    item.value = await fetchWanted(id.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '불러오지 못했습니다.'
    item.value = null
  } finally {
    loading.value = false
  }
}

watch(id, () => {
  if (!auth.isLoggedIn) return
  load()
})

watch(
  () => auth.isLoggedIn,
  (loggedIn) => {
    if (loggedIn) load()
    else {
      item.value = null
      error.value = ''
      loading.value = false
    }
  },
)

onMounted(() => {
  load()
})

async function onOpenChat() {
  if (!item.value || item.value.is_owner) return
  try {
    const { room_id } = await openChatRoom({ kind: 'wanted', wanted_id: item.value.wanted_id })
    error.value = ''
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
  <div v-if="!auth.isLoggedIn" class="login-gate">
    <p class="login-gate-title">구매 희망글 상세는 로그인 후 확인할 수 있습니다.</p>
    <p class="login-gate-text">같은 학교로 등록된 회원의 게시글만 열람할 수 있습니다.</p>
    <div class="login-gate-actions">
      <RouterLink class="btn primary" :to="{ name: 'login', query: { redirect: route.fullPath } }">
        로그인
      </RouterLink>
      <RouterLink class="btn" to="/register">회원가입</RouterLink>
    </div>
  </div>
  <p v-else-if="loading" class="loading-page">불러오는 중…</p>
  <div v-else-if="item" class="detail">
    <nav class="crumb">
      <span class="crumb-muted">목록</span>
      <span aria-hidden="true"> / </span>
      <span>상세</span>
    </nav>

    <p v-if="error" class="err" role="alert">{{ error }}</p>

    <div class="layout">
      <div class="gallery">
        <div class="wanted-panel" aria-hidden="true">
          <span class="wanted-panel__glow" />
          <span class="wanted-panel__icon">🔍</span>
          <span class="wanted-panel__badge">구매 희망</span>
        </div>
      </div>

      <aside class="summary">
        <h1 class="title">{{ item.title }}</h1>
        <p class="price">{{ formatMaxPrice(item.max_price) }}</p>
        <div class="meta-row">
          <span class="chip chip-wanted">구매 희망</span>
        </div>

        <div class="seller-block">
          <span class="label">작성자</span>
          <RouterLink
            v-if="item.is_owner"
            class="seller-profile"
            :to="{ name: 'my-shop' }"
          >
            <span class="seller-av-wrap">
              <span class="seller-av seller-av--ph" aria-hidden="true">{{
                (item.author_name || '?').slice(0, 1)
              }}</span>
            </span>
            <span class="seller-name">{{ item.author_name }}</span>
          </RouterLink>
          <RouterLink
            v-else
            class="seller-profile"
            :to="{ name: 'user-shop', params: { userId: item.user_id } }"
          >
            <span class="seller-av-wrap">
              <span class="seller-av seller-av--ph" aria-hidden="true">{{
                (item.author_name || '?').slice(0, 1)
              }}</span>
            </span>
            <span class="seller-name">{{ item.author_name }}</span>
          </RouterLink>
        </div>

        <p v-if="item.preferred_location" class="loc">
          <span class="label">희망 장소</span>
          {{ item.preferred_location }}
        </p>

        <div v-if="auth.isLoggedIn" class="actions">
          <button
            v-if="!item.is_owner"
            type="button"
            class="btn primary"
            @click="onOpenChat"
          >
            판매하기
          </button>
          <p v-if="!item.is_owner" class="sell-hint">
            판매를 제안하며 작성자와 채팅을 시작합니다.
          </p>

          <template v-if="item.is_owner">
            <button type="button" class="btn danger" :disabled="deleting" @click="remove">
              {{ deleting ? '삭제 중…' : '삭제' }}
            </button>
          </template>
        </div>
      </aside>
    </div>

    <section class="description-block" aria-labelledby="wanted-desc-heading">
      <h2 id="wanted-desc-heading" class="description-block__title">상세 설명</h2>
      <div
        class="description-block__body"
        :class="{ 'description-block__body--empty': !item.description?.trim() }"
      >
        <p v-if="item.description?.trim()" class="description-block__text">{{ item.description }}</p>
        <p v-else class="description-block__empty">작성자가 상세 설명을 등록하지 않았습니다.</p>
      </div>
    </section>
  </div>

  <p v-else class="err">{{ error || '게시글을 찾을 수 없습니다.' }}</p>
</template>

<style scoped>
.detail {
  width: 100%;
  max-width: 100%;
  margin: 0;
  padding: 0 clamp(0.75rem, 4vw, 3rem) 2.25rem;
  box-sizing: border-box;
}

.crumb {
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.crumb a {
  color: var(--color-heading);
  font-weight: 600;
}

.crumb-muted {
  color: var(--color-text);
  opacity: 0.65;
}

.err {
  color: #c0392b;
  margin-bottom: 1rem;
}

.layout {
  display: grid;
  gap: 1.25rem 1rem;
  grid-template-columns: 1fr;
}

.gallery {
  min-width: 0;
}

.wanted-panel {
  position: relative;
  width: 100%;
  box-sizing: border-box;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid var(--color-border);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  aspect-ratio: 16 / 10;
  max-height: 420px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(
    145deg,
    rgba(var(--color-accent-rgb), 0.3) 0%,
    rgba(var(--color-accent-rgb), 0.09) 45%,
    var(--color-background-mute) 100%
  );
}

.wanted-panel__glow {
  position: absolute;
  inset: -35%;
  background: radial-gradient(circle at 28% 18%, rgba(255, 255, 255, 0.16) 0%, transparent 52%);
  pointer-events: none;
}

.wanted-panel__icon {
  position: relative;
  font-size: clamp(2.5rem, 8vw, 3.25rem);
  line-height: 1;
  filter: drop-shadow(0 2px 10px rgba(0, 0, 0, 0.1));
  opacity: 0.92;
}

.wanted-panel__badge {
  position: absolute;
  left: 0.75rem;
  top: 0.75rem;
  padding: 0.2rem 0.55rem;
  font-size: 0.78rem;
  font-weight: 600;
  border-radius: 999px;
  background: hsla(186, 42%, 22%, 0.92);
  color: #fff;
  letter-spacing: -0.02em;
}

@media (min-width: 900px) {
  .layout {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    column-gap: clamp(0.75rem, 1.2vw, 1.25rem);
    row-gap: 1.25rem;
    align-items: start;
  }

  .summary {
    position: sticky;
    top: 0.75rem;
  }
}

@media (min-width: 1200px) {
  .layout {
    column-gap: clamp(1rem, 1.8vw, 1.5rem);
  }
}

.summary {
  width: 100%;
  min-width: 0;
  padding: 1.25rem 1.35rem;
  border-radius: 14px;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.04);
  box-sizing: border-box;
}

.title {
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0 0 0.65rem;
  color: var(--color-heading);
  line-height: 1.35;
}

.price {
  font-size: 1.5rem;
  font-weight: 800;
  margin: 0 0 1rem;
  letter-spacing: -0.02em;
  color: var(--color-heading);
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin-bottom: 1rem;
}

.chip {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 600;
}

.chip-wanted {
  background: hsla(186, 38%, 88%, 1);
  color: hsl(186, 42%, 26%);
  border: 1px solid rgba(var(--color-accent-rgb), 0.35);
}

@media (prefers-color-scheme: dark) {
  .chip-wanted {
    background: hsla(186, 28%, 18%, 1);
    color: hsla(186, 55%, 72%, 1);
  }
}

.seller-block,
.loc {
  font-size: 0.95rem;
  margin: 0 0 0.75rem;
  line-height: 1.5;
}

.seller-block .label,
.loc .label {
  display: block;
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  opacity: 0.65;
  margin-bottom: 0.15rem;
}

.seller-profile {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: inherit;
  border-radius: 10px;
  padding: 0.25rem 0.35rem;
  margin: -0.25rem -0.35rem;
  transition: background 0.15s;
}

.seller-profile:hover {
  background: rgba(92, 176, 185, 0.12);
}

.seller-av {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid var(--color-border);
}

.seller-av--ph {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.95rem;
  font-weight: 700;
  background: var(--color-background-mute);
  color: var(--color-heading);
}

.seller-name {
  font-weight: 600;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 1.25rem;
  align-items: center;
}

.sell-hint {
  width: 100%;
  margin: 0;
  font-size: 0.86rem;
  line-height: 1.45;
  color: var(--color-text);
  opacity: 0.88;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem 0.9rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
  color: var(--color-text);
  font-size: 0.9rem;
  cursor: pointer;
  text-decoration: none;
}

.btn:hover {
  border-color: var(--color-border-hover);
}

.btn.primary {
  background: var(--color-accent);
  border-color: transparent;
  color: #fff;
}

.btn.danger {
  border-color: #c0392b;
  color: #c0392b;
}

.description-block {
  margin-top: 2rem;
}

.description-block__title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-heading);
  margin: 0 0 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid rgba(92, 176, 185, 0.35);
}

.description-block__body {
  min-height: auto;
  padding: 1.35rem clamp(1rem, 3vw, 2rem) 1.6rem;
  border-radius: 14px;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

.description-block__body--empty {
  min-height: 6.5rem;
}

.description-block__text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 1.05rem;
  line-height: 1.8;
  color: var(--color-text);
}

.description-block__empty {
  margin: 0;
  font-size: 0.98rem;
  line-height: 1.65;
  color: var(--color-text);
  opacity: 0.7;
  font-style: italic;
}

.login-gate {
  padding: 2.5rem 1.5rem;
  text-align: center;
  border-radius: 12px;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
  max-width: 480px;
  margin: 0 auto;
}

.login-gate-title {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--color-heading);
  margin-bottom: 0.5rem;
}

.login-gate-text {
  font-size: 0.92rem;
  color: var(--color-text);
  opacity: 0.9;
  margin-bottom: 1.25rem;
  line-height: 1.5;
}

.login-gate-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
}

.login-gate-actions .btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem 0.9rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
  color: var(--color-text);
  font-size: 0.9rem;
  text-decoration: none;
}

.login-gate-actions .btn.primary {
  background: var(--color-accent);
  border-color: transparent;
  color: #fff;
}

.login-gate-actions .btn.ghost {
  background: transparent;
}

.loading-page {
  padding: 2rem;
  text-align: center;
  font-size: 0.95rem;
}
</style>
