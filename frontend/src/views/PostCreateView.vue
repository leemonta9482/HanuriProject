<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { createBoard } from '@/api/boards'
import { createWanted } from '@/api/wanted'
import type { TradeType } from '@/api/types'

const route = useRoute()
const router = useRouter()

type PostKind = 'board' | 'wanted'
const kind = ref<PostKind>('board')

const title = ref('')
const description = ref('')
const location = ref('')
const tradeType = ref<TradeType>('BOTH')
const price = ref(0)
const files = ref<File[]>([])

const maxPrice = ref<number | ''>('')
const preferredLocation = ref('')

const error = ref('')
const loading = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

function syncKindFromRoute() {
  kind.value = route.query.type === 'wanted' ? 'wanted' : 'board'
}

onMounted(syncKindFromRoute)
watch(() => route.query.type, syncKindFromRoute)

watch(kind, (k) => {
  void router.replace({ path: '/write', query: k === 'wanted' ? { type: 'wanted' } : {} })
})

function onCancelWrite() {
  router.back()
}

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

async function submit() {
  error.value = ''
  if (!title.value.trim()) {
    error.value = '제목을 입력해 주세요.'
    return
  }
  loading.value = true
  try {
    if (kind.value === 'board') {
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
    } else {
      const w = await createWanted({
        title: title.value.trim(),
        description: description.value.trim() || null,
        max_price:
          maxPrice.value === '' || maxPrice.value === null ? null : Number(maxPrice.value),
        preferred_location: preferredLocation.value.trim() || null,
      })
      await router.push({ name: 'wanted-detail', params: { id: String(w.wanted_id) } })
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '저장에 실패했습니다.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="write-page">
    <header class="write-head">
      <nav class="crumb" aria-label="경로">
        <span class="crumb-muted">거래 목록</span>
        <span class="crumb-sep" aria-hidden="true">/</span>
        <span class="crumb-here">글 작성</span>
      </nav>
      <div class="head-inner">
        <h1 class="page-title">새 글 작성</h1>
        <p class="lead">
          판매할 물건이나 구매하고 싶은 물건을 선택하여 게시글을 올려보세요!
        </p>
      </div>
    </header>

    <div class="write-card">
      <div class="card-top">
        <p class="card-label">글 유형</p>
        <div class="kind-segment" role="radiogroup" aria-label="판매 또는 구매 희망">
          <label class="seg" :class="{ active: kind === 'board' }">
            <input v-model="kind" class="sr-only" type="radio" name="kind" value="board" />
            <span class="seg-icon" aria-hidden="true">📦</span>
            <span class="seg-text">
              <span class="seg-title">판매글</span>
              <span class="seg-desc">중고 물품 판매</span>
            </span>
          </label>
          <label class="seg" :class="{ active: kind === 'wanted' }">
            <input v-model="kind" class="sr-only" type="radio" name="kind" value="wanted" />
            <span class="seg-icon" aria-hidden="true">🔍</span>
            <span class="seg-text">
              <span class="seg-title">구매 희망</span>
              <span class="seg-desc">사고 싶은 물건 요청</span>
            </span>
          </label>
        </div>
      </div>

      <p v-if="error" class="alert" role="alert">{{ error }}</p>

      <form class="form" @submit.prevent="submit">
        <section class="section" :aria-labelledby="kind === 'board' ? 'sec-board' : 'sec-wanted'">
          <h2 :id="kind === 'board' ? 'sec-board' : 'sec-wanted'" class="section-title">
            {{ kind === 'board' ? '판매 정보' : '구매 희망 정보' }}
          </h2>

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

          <template v-if="kind === 'board'">
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
              <select v-model="tradeType" class="select-theme select-theme--block">
                <option value="DIRECT">직거래만</option>
                <option value="DELIVERY">택배만</option>
                <option value="BOTH">직거래·택배 모두</option>
              </select>
            </label>

            <div class="field">
              <span class="label">사진</span>
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
          </template>

          <template v-else>
            <label class="field">
              <span class="label">설명</span>
              <textarea
                v-model="description"
                class="input textarea"
                rows="5"
                maxlength="8000"
                placeholder="원하는 물건, 상태, 예산에 대한 설명을 적어 주세요"
              />
            </label>
            <label class="field">
              <span class="label">희망 최대 가격</span>
              <p class="hint">비워 두면 가격은 미정으로 표시됩니다.</p>
              <div class="input-with-unit">
                <input v-model.number="maxPrice" class="input" type="number" min="0" placeholder="미정" />
                <span class="unit">원</span>
              </div>
            </label>
            <label class="field">
              <span class="label">희망 거래 지역·장소</span>
              <input
                v-model="preferredLocation"
                class="input"
                maxlength="255"
                type="text"
                placeholder="예: 캠퍼스 내, 근처 역"
              />
            </label>
          </template>
        </section>

        <div class="actions">
          <button type="button" class="btn ghost" @click="onCancelWrite">취소</button>
          <button type="submit" class="btn primary" :disabled="loading">
            {{ loading ? '등록 중…' : '등록하기' }}
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
  color: hsl(186, 38%, 30%);
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
}

.head-inner {
  padding: 1.25rem 1.35rem;
  border-radius: 14px;
  background: linear-gradient(
    135deg,
    hsla(186, 30%, 94%, 1) 0%,
    hsla(200, 35%, 96%, 1) 100%
  );
  border: 1px solid var(--color-border);
}

@media (prefers-color-scheme: dark) {
  .head-inner {
    background: linear-gradient(
      135deg,
      hsla(186, 18%, 14%, 1) 0%,
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

.kind-segment {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.65rem;
}

@media (max-width: 480px) {
  .kind-segment {
    grid-template-columns: 1fr;
  }
}

.seg {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  padding: 0.85rem 1rem;
  border-radius: 12px;
  border: 2px solid var(--color-border);
  background: var(--color-background);
  cursor: pointer;
  transition:
    border-color 0.2s,
    box-shadow 0.2s,
    background 0.2s;
}

.seg:hover {
  border-color: var(--color-border-hover);
}

.seg.active {
  border-color: rgba(92, 176, 185, 0.65);
  background: hsl(186, 28%, 97%);
  box-shadow: 0 0 0 1px rgba(92, 176, 185, 0.2);
}

@media (prefers-color-scheme: dark) {
  .seg.active {
    background: hsl(186, 20%, 14%);
    box-shadow: 0 0 0 1px rgba(92, 176, 185, 0.35);
  }
}

.seg-icon {
  font-size: 1.35rem;
  line-height: 1;
}

.seg-text {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.seg-title {
  font-size: 0.98rem;
  font-weight: 700;
  color: var(--color-heading);
}

.seg-desc {
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

.field:last-child {
  margin-bottom: 0;
}

.label {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--color-heading);
}

.req {
  color: hsl(186, 38%, 32%);
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
  border-color: rgba(92, 176, 185, 0.55);
  box-shadow: 0 0 0 3px rgba(92, 176, 185, 0.15);
}

.textarea {
  resize: vertical;
  min-height: 120px;
  line-height: 1.5;
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
  border-right: 1px solid rgba(92, 176, 185, 0.55);
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
  border-color: rgba(92, 176, 185, 0.45);
  background: hsl(186, 25%, 98%);
}

@media (prefers-color-scheme: dark) {
  .dropzone:hover {
    background: hsl(186, 15%, 12%);
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
  color: hsl(186, 38%, 30%);
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  text-decoration: underline;
}

.file-remove:hover {
  color: hsl(186, 38%, 24%);
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
  background: linear-gradient(180deg, hsl(186, 40%, 52%), hsl(186, 38%, 44%));
  color: #fff;
  box-shadow: 0 2px 8px rgba(92, 176, 185, 0.35);
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
