<script setup lang="ts">
import { computed, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { AGREEMENTS, isPublicLegalDocKey, type PublicLegalDocKey } from '@/legal/agreements'

const router = useRouter()
const route = useRoute()

const PAGE_TITLES: Record<PublicLegalDocKey, string> = {
  tos: '이용약관',
  privacy: '개인정보처리방침',
  community: '운영정책(커뮤니티 규칙)',
  marketing: '마케팅 정보 수신',
}

const navItems = AGREEMENTS.filter(
  (a) => isPublicLegalDocKey(a.key) && a.body != null && a.body.length > 0,
).map((a) => ({
  key: a.key as PublicLegalDocKey,
  title: PAGE_TITLES[a.key as PublicLegalDocKey],
}))

const docParam = computed(() => String(route.params.doc ?? ''))

watch(
  docParam,
  (k) => {
    if (!isPublicLegalDocKey(k)) {
      void router.replace({ name: 'legal-doc', params: { doc: 'tos' } })
    }
  },
  { immediate: true },
)

const activeDoc = computed(() => {
  const k = docParam.value
  if (!isPublicLegalDocKey(k)) return null
  return AGREEMENTS.find((x) => x.key === k) ?? null
})

const bodyText = computed(() => activeDoc.value?.body ?? '')

/** 이중 줄바꿈 기준 문단 — 전문 길게 펼쳐 보기 좋게 */
const bodyParagraphs = computed(() =>
  bodyText.value
    .split(/\n{2,}/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0),
)

const pageHeading = computed(() => {
  const k = docParam.value
  return isPublicLegalDocKey(k) ? PAGE_TITLES[k] : '약관 및 정책'
})
</script>

<template>
  <div class="legal">
    <header class="legal-head">
      <RouterLink class="legal-back" to="/">홈으로</RouterLink>
      <h1 class="legal-h1">{{ pageHeading }}</h1>
      <p class="legal-lead">
        회원가입 시 동의 화면과 동일한 전문입니다. 최신 내용은 본 페이지를 기준으로 합니다.
      </p>
    </header>

    <nav class="legal-nav" aria-label="약관·정책 목록">
      <RouterLink
        v-for="item in navItems"
        :key="item.key"
        :to="{ name: 'legal-doc', params: { doc: item.key } }"
        class="legal-nav-item"
        :class="{ 'legal-nav-item--active': docParam === item.key }"
      >
        {{ item.title }}
      </RouterLink>
    </nav>

    <article class="legal-article" aria-labelledby="legal-doc-title">
      <h2 id="legal-doc-title" class="sr-only">{{ pageHeading }} 전문</h2>
      <div class="legal-prose">
        <p v-for="(para, idx) in bodyParagraphs" :key="idx" class="legal-p">{{ para }}</p>
      </div>
    </article>
  </div>
</template>

<style scoped>
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.legal {
  width: 100%;
  max-width: var(--hanuri-page-max-width);
  margin: 0 auto;
  padding-bottom: 1.5rem;
}

.legal-head {
  margin-bottom: 1.25rem;
}

.legal-back {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.75rem;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 8px;
  background: var(--color-accent);
  color: #fff;
  font-weight: 600;
  font-size: 1rem;
  text-decoration: none;
  cursor: pointer;
  transition: filter 0.2s;
  box-sizing: border-box;
}

@media (hover: hover) {
  .legal-back:hover {
    filter: brightness(1.05);
    text-decoration: none;
    text-shadow: none;
  }
}

.legal-back:focus-visible {
  outline: 2px solid rgba(92, 176, 185, 0.45);
  outline-offset: 2px;
}

.legal-h1 {
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--color-heading);
  margin-bottom: 0.5rem;
  line-height: 1.35;
}

.legal-lead {
  font-size: 0.875rem;
  color: var(--color-text);
  opacity: 0.85;
  line-height: 1.55;
  max-width: 40rem;
}

.legal-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-border);
}

.legal-nav-item {
  display: inline-flex;
  align-items: center;
  padding: 0.38rem 0.75rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  background: var(--color-background-soft);
  color: var(--color-text);
  font-size: 0.8125rem;
  text-decoration: none;
}

.legal-nav-item--active {
  border-color: rgba(var(--color-accent-rgb), 0.45);
  background: rgba(var(--color-accent-rgb), 0.1);
  font-weight: 600;
  color: var(--color-heading);
}

@media (hover: hover) {
  .legal-nav-item:hover {
    border-color: var(--color-border-hover);
    text-shadow: none;
  }
}

.legal-article {
  border: 1px solid var(--color-border);
  border-radius: 10px;
  background: var(--color-background-soft);
  padding: clamp(1.25rem, 4vw, 2rem);
}

.legal-prose {
  max-width: none;
}

.legal-p {
  margin: 0 0 1.1rem;
  font-size: 0.875rem;
  line-height: 1.75;
  white-space: pre-line;
  word-break: keep-all;
  overflow-wrap: break-word;
  color: var(--color-text);
  tab-size: 2;
}

.legal-p:last-child {
  margin-bottom: 0;
}

@media (min-width: 768px) {
  .legal-p {
    font-size: 0.9375rem;
    line-height: 1.78;
  }
}
</style>
