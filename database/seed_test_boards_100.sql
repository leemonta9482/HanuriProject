-- 테스트용 판매 게시글 100건 (MySQL 8.0+ 재귀 CTE 사용)
-- 실행 전: User 테이블에 최소 1명의 회원이 있어야 합니다 (FK).
-- 승인된 회원 우선, 없으면 아무 user_id나 사용합니다.

USE HanuriProject;

SET @author := (
  SELECT user_id FROM User WHERE registration_status = 'APPROVED' LIMIT 1
);
SET @author := IFNULL(
  @author,
  (SELECT user_id FROM User LIMIT 1)
);

-- 회원이 없으면 아래에서 오류가 납니다. 먼저 회원가입·승인 후 실행하세요.

INSERT INTO Board (
  user_id,
  title,
  price,
  description,
  location,
  trade_type,
  status
)
WITH RECURSIVE seq AS (
  SELECT 1 AS n
  UNION ALL
  SELECT n + 1 FROM seq WHERE n < 100
)
SELECT
  @author,
  CONCAT('[테스트] 더미 상품 ', LPAD(n, 3, '0')),
  3000 + (n * 791) % 997000,
  '더미 데이터입니다.',
  CONCAT('캠퍼스 장소 ', n),
  ELT((n % 3) + 1, 'DIRECT', 'DELIVERY', 'BOTH'),
  ELT((n % 3) + 1, 'ON_SALE', 'RESERVED', 'SOLD')
FROM seq;

-- 확인
-- SELECT COUNT(*) FROM Board WHERE title LIKE '[테스트] 더미 상품%';
-- SELECT board_id, title, price, status FROM Board ORDER BY board_id DESC LIMIT 10;
