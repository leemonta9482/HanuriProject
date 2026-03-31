<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { fetchMyFavorites } from '@/api/boards'
import { uploadsPublicUrl } from '@/api/client'
import type { BoardListItem } from '@/api/types'

const items = ref<BoardListItem[]>([])
const error = ref('')
const loading = ref(true)

function thumbUrl(path: string | null): string | null {
  if (!path) return null
  return uploadsPublicUrl(path)
}

function formatPrice(n: number): string {
  return new Intl.NumberFormat('ko-KR').format(n) + '원'
}

onMounted(async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await fetchMyFavorites(1, 48)
    items.value = res.items
  } catch (e) {
    error.value = e instanceof Error ? e.message : '목록을 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="market">
    <header class="toolbar">
      <h1 class="title">찜한 상품</h1>
      <div class="actions">
        <RouterLink class="btn primary" to="/write">글 작성</RouterLink>
        <RouterLink class="btn" to="/" aria-label="중고 거래 목록으로 이동">중고 거래</RouterLink>
      </div>
    </header>
    <p v-if="loading">불러오는 중…</p>
    <p v-else-if="error" class="err">{{ error }}</p>
    <ul v-else class="grid">
      <li v-for="it in items" :key="it.board_id" class="card-wrap">
        <RouterLink :to="`/boards/${it.board_id}`" class="card">
          <div class="thumb" :class="{ empty: !it.thumbnail_path }">
            <img v-if="thumbUrl(it.thumbnail_path)" :src="thumbUrl(it.thumbnail_path)!" alt="" />
            <span v-else class="ph">이미지 없음</span>
          </div>
          <div class="meta">
            <p class="card-title">{{ it.title }}</p>
            <p class="price">{{ formatPrice(it.price) }}</p>
          </div>
        </RouterLink>
      </li>
    </ul>
    <p v-if="!loading && !error && items.length === 0" class="empty">찜한 상품이 없습니다.</p>
  </div>
</template>

<style scoped>
.market {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 0.5rem 2rem;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.title {
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--color-heading);
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.45rem 0.85rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
  color: var(--color-text);
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
}

.btn:hover {
  border-color: var(--color-border-hover);
}

.btn.primary {
  background: hsla(160, 100%, 37%, 1);
  border-color: transparent;
  color: #fff;
}

.btn.primary:hover {
  filter: brightness(1.05);
}

.err {
  color: #c0392b;
}

.grid {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

@media (max-width: 1024px) {
  .grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.65rem;
  }
}

@media (max-width: 480px) {
  .grid {
    gap: 0.5rem;
  }

  .card-title {
    font-size: 0.88rem;
  }

  .price {
    font-size: 0.92rem;
  }

  .meta {
    padding: 0.5rem 0.55rem 0.65rem;
  }
}

.card {
  display: block;
  text-decoration: none;
  color: inherit;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
}

.thumb {
  aspect-ratio: 4 / 3;
  background: var(--color-background-mute);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.ph {
  font-size: 0.85rem;
  opacity: 0.7;
}

.meta {
  padding: 0.65rem 0.75rem 0.85rem;
}

.card-title {
  font-weight: 600;
  font-size: 0.95rem;
}

.price {
  margin-top: 0.35rem;
  font-weight: 700;
}

.empty {
  text-align: center;
  padding: 2rem;
  opacity: 0.85;
}
</style>
