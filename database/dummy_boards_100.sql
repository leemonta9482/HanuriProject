-- 판매 게시글(Board) 더미 데이터 100건
-- 전제: User 테이블에 최소 1명 이상 존재해야 합니다.
-- 실행: mysql 클라이언트 또는 Workbench에서 HanuriProject DB 선택 후 실행

USE HanuriProject;

INSERT INTO Board (
    user_id,
    title,
    price,
    description,
    location,
    trade_type,
    status
)
SELECT
    u.user_id,
    CONCAT('[더미] 중고상품 ', LPAD(seq.n, 3, '0')),
    3000 + (seq.n * 791) % 497000,
    CONCAT(
        '자동 생성된 테스트용 설명입니다. ',
        '번호 ', seq.n,
        ' · 상태/거래방식은 행마다 다르게 분포됩니다.'
    ),
    ELT(1 + (seq.n % 5), '캠퍼스 정문', '학생회관 1층', '중앙도서관 앞', '기숙사 매점', '운동장 인근'),
    ELT(1 + (seq.n % 3), 'DIRECT', 'DELIVERY', 'BOTH'),
    ELT(1 + (seq.n % 3), 'ON_SALE', 'RESERVED', 'SOLD')
FROM (
    SELECT a.n + b.n * 10 + 1 AS n
    FROM
        (SELECT 0 AS n UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4
         UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) a,
        (SELECT 0 AS n UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4
         UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) b
) seq
CROSS JOIN (SELECT user_id FROM User ORDER BY user_id LIMIT 1) u
WHERE seq.n <= 100;
