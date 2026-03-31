-- 테스트용 판매 게시글 20건
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
) VALUES
  (@author, '[테스트] 전공 서적 세트 A', 15000, '더미 데이터입니다.', '공학관 1층 로비', 'BOTH', 'ON_SALE'),
  (@author, '[테스트] 무선 마우스', 8000, '더미 데이터입니다.', '도서관 앞', 'DIRECT', 'ON_SALE'),
  (@author, '[테스트] 기계설계 실습복 M', 12000, '더미 데이터입니다.', '학생회관', 'BOTH', 'ON_SALE'),
  (@author, '[테스트] 공학용 계산기', 45000, '더미 데이터입니다.', '캠퍼스 정문', 'DIRECT', 'RESERVED'),
  (@author, '[테스트] 노트북 거치대', 7000, '더미 데이터입니다.', '인문관', 'DELIVERY', 'ON_SALE'),
  (@author, '[테스트] USB-C 케이블 2m', 5000, '더미 데이터입니다.', '기숙사 A동', 'BOTH', 'ON_SALE'),
  (@author, '[테스트] 이어폰 (유선)', 15000, '더미 데이터입니다.', '후문 편의점 앞', 'DIRECT', 'SOLD'),
  (@author, '[테스트] 미니 선풍기', 22000, '더미 데이터입니다.', '중앙광장', 'BOTH', 'ON_SALE'),
  (@author, '[테스트] 독서대', 6000, '더미 데이터입니다.', '열람실 앞', 'DIRECT', 'ON_SALE'),
  (@author, '[테스트] 필기용 태블릿 액정필름', 9000, '더미 데이터입니다.', '전자관', 'DELIVERY', 'ON_SALE'),
  (@author, '[테스트] 캠퍼스 후드 M', 18000, '더미 데이터입니다.', '체육관', 'BOTH', 'ON_SALE'),
  (@author, '[테스트] 보조배터리 10000mAh', 25000, '더미 데이터입니다.', '학식당 입구', 'DIRECT', 'ON_SALE'),
  (@author, '[테스트] 키보드 커버 (맥북 13)', 11000, '더미 데이터입니다.', 'IT관', 'DELIVERY', 'ON_SALE'),
  (@author, '[테스트] 책상 스탠드 조명', 19000, '더미 데이터입니다.', '기숙사 B동', 'BOTH', 'RESERVED'),
  (@author, '[테스트] 공학도면 가방', 14000, '더미 데이터입니다.', '설계실 복도', 'DIRECT', 'ON_SALE'),
  (@author, '[테스트] 블루투스 스피커', 32000, '더미 데이터입니다.', '음악동', 'BOTH', 'ON_SALE'),
  (@author, '[테스트] 수학 교재 1권', 5000, '더미 데이터입니다.', '자연과학관', 'DIRECT', 'ON_SALE'),
  (@author, '[테스트] 멀티탭 6구', 13000, '더미 데이터입니다.', '전기실습실 앞', 'DELIVERY', 'ON_SALE'),
  (@author, '[테스트] 노트 정리 바인더', 4000, '더미 데이터입니다.', '문구점 앞', 'BOTH', 'ON_SALE'),
  (@author, '[테스트] 캠퍼스 지도·굿즈', 10000, '더미 데이터입니다.', '학생처 앞', 'DIRECT', 'ON_SALE');

-- 확인
-- SELECT board_id, title, price, status FROM Board ORDER BY board_id DESC LIMIT 20;
