<script setup lang="ts">
import { RouterLink } from 'vue-router'

/** 사이트 공통 하단 정보(법정 표기 형식 참고, 사업자번호는 추후 반영) */
const FOOTER = {
  representative: '이우진',
  phoneDisplay: '010-0000-0000',
  phoneTel: '010-0000-0000',
  /** 명지전문대학 캠퍼스 소재지(공개 안내 기준) */
  address: '(03656) 서울특별시 서대문구 가좌로 134 (홍은2동 356-1) 명지전문대학',
} as const
</script>

<template>
  <footer class="site-footer" role="contentinfo">
    <div class="site-footer-inner">
      <!-- 상단: 가로 링크 바 (좌측 정렬 · 구분선) -->
      <nav class="footer-top-nav" aria-label="약관 및 정책">
        <RouterLink class="ft-link ft-link--strong" :to="{ name: 'legal-doc', params: { doc: 'tos' } }">
          이용약관
        </RouterLink>
        <span class="ft-div" aria-hidden="true">|</span>
        <RouterLink class="ft-link ft-link--strong" :to="{ name: 'legal-doc', params: { doc: 'privacy' } }">
          개인정보처리방침
        </RouterLink>
        <span class="ft-div" aria-hidden="true">|</span>
        <RouterLink class="ft-link" :to="{ name: 'legal-doc', params: { doc: 'community' } }">
          운영정책
        </RouterLink>
        <span class="ft-div" aria-hidden="true">|</span>
        <RouterLink class="ft-link" :to="{ name: 'legal-doc', params: { doc: 'marketing' } }">
          마케팅 정보 수신
        </RouterLink>
      </nav>

      <div class="footer-hr" role="presentation" />

      <!-- 브랜드 한 줄 -->
      <p class="footer-brand-row">
        <strong class="footer-brand-name">하누리</strong>
        <span class="footer-brand-desc">캠퍼스(학교) 단위 중고거래 서비스</span>
      </p>

      <!-- 본문: 2열 (좌 사업자 / 우 고객 안내) -->
      <div class="footer-main-grid">
        <section class="footer-col footer-col--biz" aria-labelledby="footer-biz-heading">
          <h2 id="footer-biz-heading" class="footer-col-heading">사업자 정보</h2>
          <dl class="footer-dl">
            <div class="footer-dl-row">
              <dt>대표자</dt>
              <dd>{{ FOOTER.representative }}</dd>
            </div>
            <div class="footer-dl-row">
              <dt>사업자등록번호</dt>
              <dd class="footer-muted">현재 미등록 · 추후 게시 예정</dd>
            </div>
            <div class="footer-dl-row">
              <dt>문의</dt>
              <dd>
                <a class="footer-tel" :href="`tel:${FOOTER.phoneTel.replace(/-/g, '')}`">{{
                  FOOTER.phoneDisplay
                }}</a>
              </dd>
            </div>
            <div class="footer-dl-row footer-dl-row--stack">
              <dt>주소</dt>
              <dd>{{ FOOTER.address }}</dd>
            </div>
          </dl>
          <p class="footer-copyright">
            © {{ new Date().getFullYear() }} 하누리. All rights reserved.
          </p>
        </section>

        <section class="footer-col footer-col--support" aria-labelledby="footer-support-heading">
          <h2 id="footer-support-heading" class="footer-col-heading">고객 안내</h2>

          <div class="footer-notice-card">
            <strong class="footer-notice-title">안전 거래 안내</strong>
            <p class="footer-notice-text">
              운영팀은 학교 피드를 제공할 뿐 거래 주선자가 아닙니다.<br>
              외부 ‘안전결제’ 등으로 유도하는 채팅은 사기에 이용될 수 있으니 주의하고,<br/>
              문제가 있다면 신고해 주세요.
            </p>
            <RouterLink class="footer-notice-more" :to="{ name: 'legal-doc', params: { doc: 'tos' } }">
              이용약관 전문 보기
            </RouterLink>
          </div>
        </section>
      </div>

      <div class="footer-hr" role="presentation" />

      <!-- 하단: 고지·팁 -->
      <div class="footer-bottom">
        <p class="footer-disclaimer">
          본 서비스는 학교 단위 중고거래 플랫폼입니다. 회원 간 거래의 이행·대금·물품 상태에 대한 책임은
          거래 당사자에게 있으며, 운영팀은 신고 처리·게시물 정리 등 플랫폼 운영 범위 내에서 조치합니다.
          사업자등록번호·통신판매 신고번호 등은 추후 명시 예정입니다.
        </p>
        <ul class="footer-bullet-list">
          <li>현장 직거래 전 상품 상태·가격을 반드시 확인해 주세요.</li>
          <li>금지 품목·부적절 게시물은 운영정책에 따라 삭제·제재될 수 있습니다.</li>
        </ul>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.site-footer {
  box-sizing: border-box;
  flex-shrink: 0;
  width: 100%;
  margin: 0;
  padding-top: 2rem;
  /* 상단과 동일 2rem + 홈 표시 줄용 safe-area */
  padding-bottom: calc(2rem + env(safe-area-inset-bottom, 0px));
  padding-left: 0;
  padding-right: 0;
  border-top: 1px solid var(--color-border);
  background-color: var(--color-background-soft);
}

.site-footer-inner {
  box-sizing: border-box;
  width: 100%;
  max-width: none;
  margin-inline: 0;
  text-align: left;
  /* 본문(.layout-shell)과 비슷한 좌우 여백 + safe-area */
  padding-left: max(5rem, env(safe-area-inset-left, 0px));
  padding-right: max(4rem, env(safe-area-inset-right, 0px));
}

@media (max-width: 480px) {
  .site-footer-inner {
    padding-left: max(4.5rem, 15vw, env(safe-area-inset-left, 0px));
    padding-right: max(4rem, 14vw, env(safe-area-inset-right, 0px));
  }
}

@media (min-width: 1024px) {
  .site-footer-inner {
    padding-left: max(6rem, env(safe-area-inset-left, 0px));
    padding-right: max(5rem, env(safe-area-inset-right, 0px));
  }
}

/* 상단 링크 */
.footer-top-nav {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem 0.5rem;
  font-size: 0.8125rem;
  line-height: 1.5;
  margin-bottom: 0.85rem;
}

.ft-link {
  color: var(--color-text);
  text-decoration: none;
  opacity: 0.88;
}

.ft-link.ft-link--strong {
  font-weight: 600;
  color: var(--color-heading);
  opacity: 1;
}

@media (hover: hover) {
  .ft-link:hover {
    color: var(--color-accent);
    opacity: 1;
    text-shadow: none;
  }
}

.ft-div {
  color: var(--color-text);
  opacity: 0.35;
  font-weight: 300;
  user-select: none;
}

.footer-hr {
  height: 0;
  margin: 0;
  border: none;
  border-top: 1px solid var(--color-border);
}

.footer-brand-row {
  margin: 0.95rem 0 1.1rem;
  font-size: 0.8125rem;
  line-height: 1.5;
  color: var(--color-text);
}

.footer-brand-name {
  color: var(--color-heading);
  font-weight: 700;
  margin-right: 0.5rem;
}

.footer-brand-desc {
  opacity: 0.82;
}

/* 2열 본문 */
.footer-main-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem 2.5rem;
  padding: 0 0 1.15rem;
}

@media (min-width: 840px) {
  .footer-main-grid {
    grid-template-columns: minmax(0, 1.2fr) minmax(0, 0.9fr);
    align-items: start;
  }
}

.footer-col-heading {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--color-heading);
  margin: 0 0 0.65rem;
  letter-spacing: -0.02em;
}

.footer-dl {
  margin: 0;
  padding: 0;
  font-size: 0.78125rem;
  line-height: 1.6;
}

.footer-dl-row {
  display: grid;
  grid-template-columns: 6.25rem minmax(0, 1fr);
  gap: 0.25rem 0.85rem;
  margin: 0 0 0.4rem;
}

.footer-dl-row:last-child {
  margin-bottom: 0;
}

@media (max-width: 419px) {
  .footer-dl-row.footer-dl-row--stack {
    grid-template-columns: 1fr;
    gap: 0.15rem 0;
  }

  .footer-dl-row.footer-dl-row--stack dd {
    padding-left: 0;
    margin-top: 0;
  }
}

.footer-dl-row dt {
  margin: 0;
  padding-left: 0.35rem;
  font-weight: 600;
  color: var(--color-heading);
}

.footer-dl-row dd {
  margin: 0;
  word-break: keep-all;
  overflow-wrap: anywhere;
  color: var(--color-text);
}

.footer-muted {
  opacity: 0.82;
}

.footer-tel {
  color: var(--color-accent);
  text-decoration: none;
}

@media (hover: hover) {
  .footer-tel:hover {
    text-decoration: underline;
    text-shadow: none;
  }
}

.footer-copyright {
  margin: 0.95rem 0 0;
  font-size: 0.6875rem;
  color: var(--color-text);
  opacity: 0.55;
  letter-spacing: 0.01em;
}

/* 우측: 안내 카드 */
.footer-notice-card {
  padding: 0.72rem 0.85rem;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-background-mute);
  font-size: 0.75rem;
  line-height: 1.55;
  color: var(--color-text);
}

.footer-notice-title {
  display: block;
  font-weight: 700;
  color: var(--color-heading);
  margin-bottom: 0.35rem;
  font-size: 0.8rem;
}

.footer-notice-text {
  margin: 0 0 0.55rem;
  opacity: 0.9;
}

.footer-notice-more {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-accent);
  text-decoration: none;
}

@media (hover: hover) {
  .footer-notice-more:hover {
    text-decoration: underline;
    text-shadow: none;
  }
}

/* 하단 고지 — 본문은 푸터 컨테이너 전체 너비 사용 */
.footer-bottom {
  box-sizing: border-box;
  width: 100%;
  padding-top: 1rem;
}

.footer-disclaimer {
  margin: 0 0 0.65rem;
  max-width: none;
  width: 100%;
  box-sizing: border-box;
  font-size: 0.6875rem;
  line-height: 1.6;
  color: var(--color-text);
  opacity: 0.62;
}

.footer-bullet-list {
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: 0.6875rem;
  line-height: 1.55;
  color: var(--color-text);
  opacity: 0.58;
}

.footer-bullet-list li {
  position: relative;
  padding-left: 0.85rem;
  margin-bottom: 0.35rem;
}

.footer-bullet-list li:last-child {
  margin-bottom: 0;
}

.footer-bullet-list li::before {
  content: '·';
  position: absolute;
  left: 0;
  opacity: 0.7;
}
</style>
