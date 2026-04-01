<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { addFavorite, deleteBoard, fetchBoard, removeFavorite, reportBoard, updateBoardStatus } from '@/api/boards'
import { openChatRoom } from '@/api/chat'
import { uploadsPublicUrl } from '@/api/client'
import type { BoardDetail } from '@/api/types'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const board = ref<BoardDetail | null>(null)
const error = ref('')
const loading = ref(false)
const reportOpen = ref(false)
const reportReason = ref('')
const statusEdit = ref(false)
/** 갤러리 대표 이미지 인덱스 */
const selectedImageIndex = ref(0)

const id = computed(() => Number(route.params.id))

const statusLabel: Record<string, string> = {
  ON_SALE: '판매중',
  RESERVED: '예약중',
  SOLD: '거래완료',
}

const tradeLabel: Record<string, string> = {
  DIRECT: '직거래',
  DELIVERY: '택배',
  BOTH: '직거래·택배',
}

function imgUrl(path: string): string {
  return uploadsPublicUrl(path)
}

async function load() {
  if (!auth.isLoggedIn) {
    board.value = null
    error.value = ''
    loading.value = false
    return
  }
  error.value = ''
  loading.value = true
  try {
    board.value = await fetchBoard(id.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '불러오지 못했습니다.'
    board.value = null
  } finally {
    loading.value = false
  }
}

watch(id, () => {
  selectedImageIndex.value = 0
  if (!auth.isLoggedIn) return
  load()
})

watch(
  () => auth.isLoggedIn,
  (loggedIn) => {
    if (loggedIn) load()
    else {
      board.value = null
      error.value = ''
      loading.value = false
    }
  },
)

onMounted(() => {
  load()
})

async function toggleFavorite() {
  if (!auth.isLoggedIn || !board.value) return
  try {
    if (board.value.is_favorited) {
      board.value = await removeFavorite(board.value.board_id)
    } else {
      board.value = await addFavorite(board.value.board_id)
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '처리 실패'
  }
}

async function onOpenChat() {
  if (!board.value) return
  try {
    const { room_id } = await openChatRoom({ kind: 'board', board_id: board.value.board_id })
    error.value = ''
    await router.push({ name: 'chat', query: { room: String(room_id) } })
  } catch (e) {
    error.value = e instanceof Error ? e.message : '채팅방을 열 수 없습니다.'
  }
}

async function onReport() {
  if (!board.value || !reportReason.value.trim()) return
  try {
    await reportBoard(board.value.board_id, reportReason.value.trim())
    reportOpen.value = false
    reportReason.value = ''
    alert('신고가 접수되었습니다.')
  } catch (e) {
    error.value = e instanceof Error ? e.message : '신고 실패'
  }
}

async function setStatus(s: 'ON_SALE' | 'RESERVED' | 'SOLD') {
  if (!board.value) return
  try {
    board.value = await updateBoardStatus(board.value.board_id, s)
    statusEdit.value = false
  } catch (e) {
    error.value = e instanceof Error ? e.message : '상태 변경 실패'
  }
}

async function onDelete() {
  if (!board.value) return
  if (!confirm('이 판매글을 삭제할까요?')) return
  try {
    await deleteBoard(board.value.board_id)
    await router.push({ name: 'home' })
  } catch (e) {
    error.value = e instanceof Error ? e.message : '삭제 실패'
  }
}

function formatPrice(n: number): string {
  return new Intl.NumberFormat('ko-KR').format(n) + '원'
}

watch(board, (b) => {
  if (b?.images?.length) {
    selectedImageIndex.value = Math.min(selectedImageIndex.value, b.images.length - 1)
  } else {
    selectedImageIndex.value = 0
  }
})

function prevGalleryImage() {
  const imgs = board.value?.images
  if (!imgs?.length) return
  const n = imgs.length
  if (n < 2) return
  selectedImageIndex.value = (selectedImageIndex.value - 1 + n) % n
}

function nextGalleryImage() {
  const imgs = board.value?.images
  if (!imgs?.length) return
  const n = imgs.length
  if (n < 2) return
  selectedImageIndex.value = (selectedImageIndex.value + 1) % n
}
</script>

<template>
  <div v-if="!auth.isLoggedIn" class="login-gate">
    <p class="login-gate-title">판매글 상세는 로그인 후 확인할 수 있습니다.</p>
    <p class="login-gate-text">같은 학교로 등록된 회원의 게시글만 열람할 수 있습니다.</p>
    <div class="login-gate-actions">
      <RouterLink class="btn primary" :to="{ name: 'login', query: { redirect: route.fullPath } }">
        로그인
      </RouterLink>
      <RouterLink class="btn" to="/register">회원가입</RouterLink>
    </div>
  </div>
  <p v-else-if="loading" class="loading-page">불러오는 중…</p>
  <div v-else-if="board" class="detail">
    <nav class="crumb">
      <span class="crumb-muted">목록</span>
      <span aria-hidden="true"> / </span>
      <span>상세</span>
    </nav>

    <p v-if="error" class="err" role="alert">{{ error }}</p>

    <div class="layout">
      <div class="gallery">
        <div v-if="board.images.length === 0" class="no-img">등록된 이미지가 없습니다.</div>
        <template v-else>
          <div class="main-img">
            <img
              :src="imgUrl(board.images[selectedImageIndex]!.path)"
              :alt="board.title"
            />
            <template v-if="board.images.length > 1">
              <button
                type="button"
                class="gallery-nav gallery-nav--prev"
                aria-label="이전 사진"
                @click="prevGalleryImage"
              >
                <span class="gallery-nav__icon" aria-hidden="true">‹</span>
              </button>
              <button
                type="button"
                class="gallery-nav gallery-nav--next"
                aria-label="다음 사진"
                @click="nextGalleryImage"
              >
                <span class="gallery-nav__icon" aria-hidden="true">›</span>
              </button>
            </template>
          </div>
          <ul v-if="board.images.length > 1" class="thumbs">
            <li v-for="(im, idx) in board.images" :key="im.image_id">
              <button
                type="button"
                class="thumb-btn"
                :class="{ 'thumb-btn--active': idx === selectedImageIndex }"
                :aria-label="`이미지 ${idx + 1}번 보기`"
                @click="selectedImageIndex = idx"
              >
                <img :src="imgUrl(im.path)" alt="" />
              </button>
            </li>
          </ul>
        </template>
      </div>

      <aside class="summary">
        <h1 class="title">{{ board.title }}</h1>
        <p class="price">{{ formatPrice(board.price) }}</p>
        <div class="meta-row">
          <span
            class="chip chip-status"
            :class="{
              'chip-status--on-sale': board.status === 'ON_SALE',
              'chip-status--reserved': board.status === 'RESERVED',
              'chip-status--sold': board.status === 'SOLD',
            }"
          >{{ statusLabel[board.status] ?? board.status }}</span>
          <span class="chip chip-trade">{{ tradeLabel[board.trade_type] ?? board.trade_type }}</span>
        </div>
        <p class="fav-count">찜 {{ board.favorite_count }}</p>
        <div class="seller-block">
          <span class="label">판매자</span>
          <RouterLink
            v-if="board.is_owner"
            class="seller-profile"
            :to="{ name: 'my-shop' }"
          >
            <span class="seller-av-wrap">
              <img
                v-if="board.seller_profile_image_path"
                :src="imgUrl(board.seller_profile_image_path)"
                alt=""
                class="seller-av"
              />
              <span v-else class="seller-av seller-av--ph" aria-hidden="true">{{
                (board.seller_name || '?').slice(0, 1)
              }}</span>
            </span>
            <span class="seller-name">{{ board.seller_name }}</span>
          </RouterLink>
          <RouterLink
            v-else
            class="seller-profile"
            :to="{ name: 'user-shop', params: { userId: board.user_id } }"
          >
            <span class="seller-av-wrap">
              <img
                v-if="board.seller_profile_image_path"
                :src="imgUrl(board.seller_profile_image_path)"
                alt=""
                class="seller-av"
              />
              <span v-else class="seller-av seller-av--ph" aria-hidden="true">{{
                (board.seller_name || '?').slice(0, 1)
              }}</span>
            </span>
            <span class="seller-name">{{ board.seller_name }}</span>
          </RouterLink>
        </div>
        <p v-if="board.location" class="loc">
          <span class="label">거래 장소</span>
          {{ board.location }}
        </p>

        <div v-if="auth.isLoggedIn" class="actions">
          <button v-if="!board.is_owner" type="button" class="btn" @click="toggleFavorite">
            {{ board.is_favorited ? '♥ 찜 해제' : '♡ 찜하기' }}
          </button>
          <button
            v-if="!board.is_owner"
            type="button"
            class="btn primary"
            @click="onOpenChat"
          >
            구매하기
          </button>

          <template v-if="board.is_owner">
            <RouterLink class="btn" :to="`/boards/${board.board_id}/edit`">수정</RouterLink>
            <button type="button" class="btn danger" @click="onDelete">삭제</button>
            <button type="button" class="btn" @click="statusEdit = !statusEdit">거래 상태 변경</button>
            <div v-if="statusEdit" class="status-btns">
              <button type="button" class="btn sm" @click="setStatus('ON_SALE')">판매중</button>
              <button type="button" class="btn sm" @click="setStatus('RESERVED')">예약중</button>
              <button type="button" class="btn sm" @click="setStatus('SOLD')">거래완료</button>
            </div>
          </template>

          <button v-if="!board.is_owner" type="button" class="btn ghost" @click="reportOpen = !reportOpen">
            신고
          </button>
        </div>
        <p v-else class="hint">로그인하면 찜·구매하기(채팅)·신고를 이용할 수 있습니다.</p>

        <div v-if="reportOpen" class="report">
          <label class="field">
            <span>신고 사유</span>
            <textarea v-model="reportReason" rows="3" maxlength="2000" placeholder="내용을 입력하세요." />
          </label>
          <button type="button" class="btn primary" :disabled="!reportReason.trim()" @click="onReport">
            제출
          </button>
        </div>
      </aside>
    </div>

    <section class="description-block" aria-labelledby="desc-heading">
      <h2 id="desc-heading" class="description-block__title">상품 설명</h2>
      <div
        class="description-block__body"
        :class="{ 'description-block__body--empty': !board.description?.trim() }"
      >
        <p v-if="board.description?.trim()" class="description-block__text">{{ board.description }}</p>
        <p v-else class="description-block__empty">판매자가 상품 설명을 등록하지 않았습니다.</p>
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

.main-img {
  position: relative;
  width: 100%;
  box-sizing: border-box;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid var(--color-border);
  background: var(--color-background-mute);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  /* 가로(열 너비)·16:10으로 높이 결정; 뷰포트 세로(vh)에 따라 변하지 않음 */
  aspect-ratio: 16 / 10;
  max-height: 420px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.main-img img {
  position: relative;
  z-index: 0;
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  display: block;
  object-fit: contain;
}

.gallery-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.75rem;
  padding: 0;
  margin: 0;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  color: #fff;
  background: rgba(0, 0, 0, 0.42);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  transition:
    background 0.15s,
    transform 0.12s;
}

.gallery-nav:hover {
  background: rgba(0, 0, 0, 0.58);
}

.gallery-nav:focus-visible {
  outline: 2px solid rgba(92, 176, 185, 0.85);
  outline-offset: 2px;
}

.gallery-nav:active {
  transform: translateY(-50%) scale(0.96);
}

.gallery-nav--prev {
  left: 0.5rem;
}

.gallery-nav--next {
  right: 0.5rem;
}

.gallery-nav__icon {
  font-size: 1.85rem;
  line-height: 1;
  font-weight: 300;
  margin-top: -0.1em;
  user-select: none;
}

@media (max-width: 480px) {
  .gallery-nav {
    width: 2.15rem;
    height: 2.4rem;
  }

  .gallery-nav--prev {
    left: 0.35rem;
  }

  .gallery-nav--next {
    right: 0.35rem;
  }

  .gallery-nav__icon {
    font-size: 1.55rem;
  }
}

.no-img {
  width: 100%;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  aspect-ratio: 16 / 10;
  max-height: 420px;
  padding: 1rem;
  text-align: center;
  border-radius: 14px;
  border: 1px dashed var(--color-border);
  box-sizing: border-box;
}

.thumbs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  list-style: none;
  padding: 0.65rem 0 0;
  margin: 0;
}

.thumb-btn {
  display: block;
  padding: 0;
  margin: 0;
  border: 2px solid transparent;
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  background: var(--color-background-mute);
  transition:
    border-color 0.15s,
    box-shadow 0.15s;
}

.thumb-btn:hover {
  border-color: var(--color-border-hover);
}

.thumb-btn--active {
  border-color: rgba(92, 176, 185, 0.75);
  box-shadow: 0 0 0 2px rgba(92, 176, 185, 0.2);
}

.thumb-btn img {
  width: 76px;
  height: 76px;
  object-fit: cover;
  display: block;
}

/* 데스크톱: 사진 영역은 고정 비율(베이스 .main-img)·이미지는 contain으로만 표시 */
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
  margin-bottom: 0.45rem;
}

.fav-count {
  margin: 0 0 1rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text);
  opacity: 0.9;
}

.chip {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 600;
}

.chip-status {
  background: var(--color-background-mute);
  color: var(--color-text);
}

/* 판매중: 초록 / 예약중: 노랑 계열 / 거래완료: 빨강 계열 */
.chip-status--on-sale {
  background: hsl(160, 45%, 92%);
  color: hsl(160, 100%, 22%);
}

.chip-status--reserved {
  background: hsla(48, 88%, 88%, 1);
  color: hsla(32, 85%, 26%, 1);
}

.chip-status--sold {
  background: hsla(0, 55%, 92%, 1);
  color: hsla(0, 55%, 34%, 1);
}

@media (prefers-color-scheme: dark) {
  .chip-status--on-sale {
    background: hsl(160, 35%, 18%);
    color: hsla(160, 65%, 62%, 1);
  }

  .chip-status--reserved {
    background: hsla(45, 45%, 18%, 1);
    color: hsla(48, 88%, 58%, 1);
  }

  .chip-status--sold {
    background: hsla(0, 40%, 22%, 1);
    color: hsla(0, 75%, 72%, 1);
  }
}

.chip-trade {
  background: var(--color-background-mute);
  color: var(--color-text);
  border: 1px solid var(--color-border);
}

.seller-block,
.loc {
  font-size: 0.95rem;
  margin: 0 0 0.5rem;
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
  /* 내용 길이에 맞추되, 빈 페이지만 약간의 최소 높이 */
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

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 1.25rem;
  align-items: center;
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

.btn.ghost {
  background: transparent;
}

.btn.sm {
  padding: 0.3rem 0.55rem;
  font-size: 0.8rem;
}

.status-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  width: 100%;
}

.hint {
  font-size: 0.88rem;
  opacity: 0.9;
}

.report {
  margin-top: 1rem;
  padding: 1rem;
  border-radius: 10px;
  border: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.9rem;
}

.field textarea {
  padding: 0.5rem 0.6rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  color: var(--color-text);
  resize: vertical;
}

.reqs {
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
}

.reqs h2 {
  font-size: 1.1rem;
  margin-bottom: 0.75rem;
}

.reqs ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.req {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem 1rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--color-border);
}

.st {
  font-size: 0.85rem;
  opacity: 0.85;
}

.req-actions {
  display: flex;
  gap: 0.35rem;
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
