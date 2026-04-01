<script setup lang="ts">
import { ref } from 'vue'

const open = ref(false)
</script>

<template>
  <section class="spec">
    <button type="button" class="toggle" @click="open = !open">
      {{ open ? '▼' : '▶' }} 이 화면에서 제공하는 기능 (기술 명세 요약)
    </button>
    <div v-if="open" class="body">
      <ul>
        <li>
          <strong>접근</strong> 로그인한 사용자만 목록·상세 열람 가능. 판매자의 학교명이 내 학교와 같을 때만 표시(관리자는 전체).
        </li>
        <li><strong>1-1</strong> 판매 제목·본문·가격·거래 방식(직거래/택배/둘 다)·희망 장소·다중 이미지 업로드</li>
        <li><strong>1-2</strong> 구매자 → 판매자 구매 신청 (요청 목록·수락/거절, 수락 시 예약중 처리)</li>
        <li><strong>1-3</strong> 찜하기 / 찜 목록 페이지</li>
        <li><strong>1-4</strong> 판매자 본인 글 수정·이미지 추가·거래 상태 변경</li>
        <li><strong>1-5</strong> 판매자 본인 글 삭제</li>
        <li><strong>1-6</strong> 판매중 / 예약중 / 거래완료 상태 변경</li>
        <li><strong>1-7</strong> 게시글 신고 (사유 입력, 동일 글 1회)</li>
        <li><strong>1-8</strong> 구매 희망글 작성·통합 거래 목록 노출·상세·삭제 (별도 구매 희망 게시판 없음)</li>
      </ul>
      <p class="note">채팅은 별도 연동 시 구매 신청과 함께 확장할 수 있습니다.</p>
    </div>
  </section>
</template>

<style scoped>
.spec {
  margin-top: 1.5rem;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  border: 1px dashed var(--color-border);
  background: var(--color-background-mute);
}

.toggle {
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  color: var(--color-heading);
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  padding: 0.25rem 0;
}

.body {
  margin-top: 0.75rem;
}

.body ul {
  margin: 0;
  padding-left: 1.1rem;
  font-size: 0.88rem;
  line-height: 1.55;
}

.note {
  margin-top: 0.75rem;
  font-size: 0.82rem;
  opacity: 0.85;
}
</style>
