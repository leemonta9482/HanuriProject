<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import {
  addBoardImages,
  createBoard,
  deleteBoardImage,
  fetchBoard,
  updateBoard,
} from '@/api/boards'
import { uploadsPublicUrl } from '@/api/client'
import type { BoardDetail, TradeType } from '@/api/types'

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => route.name === 'board-edit')
const boardId = computed(() => (isEdit.value ? Number(route.params.id) : 0))

const title = ref('')
const price = ref(0)
const description = ref('')
const location = ref('')
const tradeType = ref<TradeType>('BOTH')
const files = ref<File[]>([])
const existing = ref<BoardDetail | null>(null)
const error = ref('')
const loading = ref(false)

const fileInput = ref<HTMLInputElement | null>(null)

function onPickFiles(e: Event) {
  const t = e.target as HTMLInputElement
  if (!t.files?.length) return
  files.value = [...files.value, ...Array.from(t.files)]
  t.value = ''
}

function removeNewFile(i: number) {
  files.value = files.value.filter((_, idx) => idx !== i)
}

function openFilePicker() {
  fileInput.value?.click()
}

function imgUrl(path: string): string {
  return uploadsPublicUrl(path)
}

async function load() {
  if (!isEdit.value) return
  loading.value = true
  error.value = ''
  try {
    const b = await fetchBoard(boardId.value)
    existing.value = b
    title.value = b.title
    price.value = b.price
    description.value = b.description ?? ''
    location.value = b.location ?? ''
    tradeType.value = b.trade_type
  } catch (e) {
    error.value = e instanceof Error ? e.message : '불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void load()
})

async function submit() {
  error.value = ''
  loading.value = true
  try {
    if (isEdit.value && existing.value) {
      await updateBoard(existing.value.board_id, {
        title: title.value.trim(),
        price: price.value,
        description: description.value.trim() || null,
        location: location.value.trim() || null,
        trade_type: tradeType.value,
      })
      if (files.value.length) {
        await addBoardImages(existing.value.board_id, files.value)
      }
      await router.push({ name: 'board-detail', params: { id: String(existing.value.board_id) } })
    } else {
      const fd = new FormData()
      fd.append('title', title.value.trim())
      fd.append('price', String(price.value))
      if (description.value.trim()) fd.append('description', description.value.trim())
      if (location.value.trim()) fd.append('location', location.value.trim())
      fd.append('trade_type', tradeType.value)
      for (const f of files.value) {
        fd.append('files', f)
      }
      const b = await createBoard(fd)
      await router.push({ name: 'board-detail', params: { id: String(b.board_id) } })
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '저장에 실패했습니다.'
  } finally {
    loading.value = false
  }
}

async function removeImage(imageId: number) {
  if (!existing.value) return
  if (!confirm('이 이미지를 삭제할까요?')) return
  loading.value = true
  error.value = ''
  try {
    const b = await deleteBoardImage(existing.value.board_id, imageId)
    existing.value = b
  } catch (e) {
    error.value = e instanceof Error ? e.message : '삭제 실패'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="write-page">
    <header class="write-head">
      <nav class="crumb" aria-label="경로">
        <RouterLink to="/" class="crumb-link">거래 목록</RouterLink>
        <span class="crumb-sep" aria-hidden="true">/</span>
        <template v-if="isEdit && existing">
          <RouterLink
            class="crumb-link"
            :to="{ name: 'board-detail', params: { id: String(existing.board_id) } }"
          >
            글 상세
          </RouterLink>
          <span class="crumb-sep" aria-hidden="true">/</span>
        </template>
        <template v-else-if="isEdit && loading">
          <span class="crumb-muted">불러오는 중…</span>
          <span class="crumb-sep" aria-hidden="true">/</span>
        </template>
        <span class="crumb-here">{{ isEdit ? '수정' : '판매글 작성' }}</span>
      </nav>
      <div class="head-inner">
        <h1 class="page-title">{{ isEdit ? '판매글 수정' : '판매글 작성' }}</h1>
        <p class="lead">
          {{
            isEdit
              ? '가격·설명·사진 등을 수정할 수 있습니다. 저장하면 상세 화면에 바로 반영됩니다.'
              : '중고 물품 정보를 입력하고 사진을 등록해 주세요.'
          }}
        </p>
      </div>
    </header>

    <div class="write-card">
      <div class="card-top">
        <p class="card-label">글 유형</p>
        <div class="edit-kind" role="status">
          <span class="edit-kind-icon" aria-hidden="true">📦</span>
          <div class="edit-kind-text">
            <span class="edit-kind-title">판매글</span>
            <span class="edit-kind-desc">{{ isEdit ? '등록한 글을 수정하는 중입니다' : '중고 물품 판매' }}</span>
          </div>
        </div>
      </div>

      <p v-if="error" class="alert" role="alert">{{ error }}</p>

      <p v-if="loading && isEdit && !existing" class="loading-inline">불러오는 중…</p>

      <form v-else class="form" @submit.prevent="submit">
        <section class="section" aria-labelledby="sec-board">
          <h2 id="sec-board" class="section-title">판매 정보</h2>

          <label class="field">
            <span class="label">제목 <span class="req">*</span></span>
            <input
              v-model="title"
              class="input"
              required
              maxlength="200"
              type="text"
              placeholder="한눈에 들어오는 제목을 적어 주세요"
            />
          </label>

          <label class="field">
            <span class="label">가격 (원) <span class="req">*</span></span>
            <div class="input-with-unit">
              <input v-model.number="price" class="input" required min="0" type="number" />
              <span class="unit">원</span>
            </div>
          </label>

          <label class="field">
            <span class="label">설명</span>
            <textarea
              v-model="description"
              class="input textarea"
              rows="5"
              maxlength="8000"
              placeholder="상품 상태, 구성품, 사용 기간 등을 적어 주세요"
            />
          </label>

          <label class="field">
            <span class="label">거래 희망 장소</span>
            <input
              v-model="location"
              class="input"
              maxlength="255"
              type="text"
              placeholder="예: 학교 정문 앞, 도서관 로비"
            />
          </label>

          <label class="field">
            <span class="label">거래 방식</span>
            <select v-model="tradeType" class="input select">
              <option value="DIRECT">직거래만</option>
              <option value="DELIVERY">택배만</option>
              <option value="BOTH">직거래·택배 모두</option>
            </select>
          </label>

          <div v-if="isEdit && existing?.images?.length" class="field">
            <span class="label">등록된 이미지</span>
            <ul class="existing-grid">
              <li v-for="im in existing.images" :key="im.image_id" class="existing-item">
                <img :src="imgUrl(im.path)" alt="" />
                <button type="button" class="existing-remove" @click="removeImage(im.image_id)">
                  삭제
                </button>
              </li>
            </ul>
          </div>

          <div class="field">
            <span class="label">{{ isEdit ? '이미지 추가' : '사진' }}</span>
            <p class="hint">최대 여러 장 · JPG, PNG, WebP, GIF</p>
            <input
              ref="fileInput"
              class="sr-only"
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif"
              multiple
              @change="onPickFiles"
            />
            <button type="button" class="dropzone" @click="openFilePicker">
              <span class="dropzone-title">이미지 추가</span>
              <span class="dropzone-sub">클릭해서 파일 선택</span>
            </button>
            <ul v-if="files.length" class="file-list">
              <li v-for="(f, i) in files" :key="i" class="file-item">
                <span class="file-name">{{ f.name }}</span>
                <button type="button" class="file-remove" @click="removeNewFile(i)">제거</button>
              </li>
            </ul>
          </div>
        </section>

        <div class="actions">
          <RouterLink class="btn ghost" to="/">취소</RouterLink>
          <button type="submit" class="btn primary" :disabled="loading">
            {{ loading ? '저장 중…' : '저장' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.write-page {
  width: 100%;
  max-width: 640px;
  margin: 0 auto;
  padding: 0 1rem 3rem;
}

.write-head {
  margin-bottom: 1.5rem;
}

.crumb {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.crumb-link {
  color: hsla(160, 100%, 30%, 1);
  font-weight: 600;
  text-decoration: none;
}

.crumb-link:hover {
  text-decoration: underline;
}

.crumb-sep {
  opacity: 0.45;
}

.crumb-here {
  color: var(--color-text);
  opacity: 0.75;
}

.crumb-muted {
  color: var(--color-text);
  opacity: 0.55;
  font-size: 0.85rem;
}

.head-inner {
  padding: 1.25rem 1.35rem;
  border-radius: 14px;
  background: linear-gradient(
    135deg,
    hsla(160, 45%, 94%, 1) 0%,
    hsla(200, 35%, 96%, 1) 100%
  );
  border: 1px solid var(--color-border);
}

@media (prefers-color-scheme: dark) {
  .head-inner {
    background: linear-gradient(
      135deg,
      hsla(160, 25%, 14%, 1) 0%,
      hsla(200, 20%, 16%, 1) 100%
    );
  }
}

.page-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-heading);
  letter-spacing: -0.02em;
  margin-bottom: 0.4rem;
}

.lead {
  font-size: 0.95rem;
  line-height: 1.55;
  color: var(--color-text);
  opacity: 0.88;
  margin: 0;
}

.write-card {
  border-radius: 16px;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

@media (prefers-color-scheme: dark) {
  .write-card {
    box-shadow: 0 4px 28px rgba(0, 0, 0, 0.35);
  }
}

.card-top {
  padding: 1.25rem 1.35rem 1rem;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-background-mute);
}

.card-label {
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-heading);
  opacity: 0.65;
  margin: 0 0 0.75rem;
}

.edit-kind {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  padding: 0.85rem 1rem;
  border-radius: 12px;
  border: 2px solid hsla(160, 100%, 37%, 0.45);
  background: hsla(160, 55%, 97%, 1);
  box-shadow: 0 0 0 1px hsla(160, 100%, 37%, 0.15);
}

@media (prefers-color-scheme: dark) {
  .edit-kind {
    background: hsla(160, 30%, 14%, 1);
    border-color: hsla(160, 50%, 32%, 0.65);
    box-shadow: 0 0 0 1px hsla(160, 50%, 28%, 0.35);
  }
}

.edit-kind-icon {
  font-size: 1.35rem;
  line-height: 1;
}

.edit-kind-text {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.edit-kind-title {
  font-size: 0.98rem;
  font-weight: 700;
  color: var(--color-heading);
}

.edit-kind-desc {
  font-size: 0.8rem;
  opacity: 0.75;
  line-height: 1.3;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}

.alert {
  margin: 0 1.35rem;
  padding: 0.65rem 0.85rem;
  border-radius: 10px;
  background: hsla(0, 70%, 96%, 1);
  color: #a93226;
  font-size: 0.9rem;
  border: 1px solid hsla(0, 50%, 88%, 1);
}

@media (prefers-color-scheme: dark) {
  .alert {
    background: hsla(0, 35%, 18%, 1);
    color: #f5b7b1;
    border-color: hsla(0, 40%, 28%, 1);
  }
}

.loading-inline {
  margin: 0;
  padding: 2rem 1.35rem;
  text-align: center;
  font-size: 0.95rem;
  color: var(--color-text);
  opacity: 0.85;
}

.form {
  padding: 1.35rem 1.35rem 1.5rem;
}

.section-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--color-heading);
  margin: 0 0 1.1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--color-border);
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-bottom: 1.1rem;
}

.field:last-of-type {
  margin-bottom: 0;
}

.label {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--color-heading);
}

.req {
  color: hsla(160, 100%, 32%, 1);
  font-weight: 700;
}

.hint {
  font-size: 0.8rem;
  opacity: 0.72;
  margin: -0.15rem 0 0.2rem;
  line-height: 1.4;
}

.input {
  padding: 0.65rem 0.85rem;
  border-radius: 10px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
  font-size: 1rem;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
}

.input::placeholder {
  opacity: 0.45;
}

.input:hover {
  border-color: var(--color-border-hover);
}

.input:focus {
  outline: none;
  border-color: hsla(160, 100%, 37%, 0.55);
  box-shadow: 0 0 0 3px hsla(160, 100%, 37%, 0.15);
}

.textarea {
  resize: vertical;
  min-height: 120px;
  line-height: 1.5;
}

.select {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23666' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.85rem center;
  padding-right: 2.25rem;
}

.input-with-unit {
  display: flex;
  align-items: stretch;
  gap: 0;
}

.input-with-unit .input {
  flex: 1;
  border-radius: 10px 0 0 10px;
  border-right: none;
}

.input-with-unit .input:focus {
  border-right: 1px solid hsla(160, 100%, 37%, 0.55);
}

.unit {
  display: flex;
  align-items: center;
  padding: 0 0.95rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text);
  opacity: 0.75;
  border: 1px solid var(--color-border);
  border-left: none;
  border-radius: 0 10px 10px 0;
  background: var(--color-background-mute);
}

.existing-grid {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(104px, 1fr));
  gap: 0.65rem;
}

.existing-item {
  position: relative;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--color-border);
  background: var(--color-background-mute);
}

.existing-item img {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  display: block;
}

.existing-remove {
  width: 100%;
  margin: 0;
  padding: 0.35rem;
  border: none;
  border-top: 1px solid var(--color-border);
  background: var(--color-background);
  color: #c0392b;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
}

.existing-remove:hover {
  background: hsla(0, 50%, 96%, 1);
}

@media (prefers-color-scheme: dark) {
  .existing-remove:hover {
    background: hsla(0, 35%, 18%, 1);
  }
}

.dropzone {
  width: 100%;
  padding: 1.15rem 1rem;
  border-radius: 12px;
  border: 2px dashed var(--color-border-hover);
  background: var(--color-background);
  cursor: pointer;
  transition:
    border-color 0.2s,
    background 0.2s;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  font: inherit;
  color: inherit;
}

.dropzone:hover {
  border-color: hsla(160, 100%, 37%, 0.45);
  background: hsla(160, 40%, 98%, 1);
}

@media (prefers-color-scheme: dark) {
  .dropzone:hover {
    background: hsla(160, 20%, 12%, 1);
  }
}

.dropzone-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--color-heading);
}

.dropzone-sub {
  font-size: 0.82rem;
  opacity: 0.65;
}

.file-list {
  list-style: none;
  padding: 0.5rem 0 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.45rem 0.65rem;
  border-radius: 8px;
  background: var(--color-background-mute);
  font-size: 0.85rem;
}

.file-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-remove {
  flex-shrink: 0;
  border: none;
  background: none;
  color: hsla(160, 100%, 30%, 1);
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  text-decoration: underline;
}

.file-remove:hover {
  color: hsla(160, 100%, 24%, 1);
}

.actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  align-items: center;
  gap: 0.65rem;
  margin-top: 1.75rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--color-border);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 2.65rem;
  padding: 0 1.35rem;
  border-radius: 10px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  border: 1px solid transparent;
  transition:
    filter 0.15s,
    opacity 0.15s;
}

.btn.primary {
  background: linear-gradient(180deg, hsla(160, 100%, 38%, 1), hsla(160, 100%, 32%, 1));
  color: #fff;
  box-shadow: 0 2px 8px hsla(160, 100%, 30%, 0.35);
}

.btn.primary:hover:not(:disabled) {
  filter: brightness(1.05);
}

.btn.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn.ghost {
  border-color: var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
}

.btn.ghost:hover {
  border-color: var(--color-border-hover);
  background: var(--color-background-mute);
}
</style>
