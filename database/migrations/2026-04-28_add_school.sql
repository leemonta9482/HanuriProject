-- 가입관리(학교 마스터) 테이블 추가 마이그레이션
-- 이미 운영 중인 DB(HanuriProject) 에 적용할 때 사용합니다.
-- 신규 환경은 main.sql 만 실행하면 자동 포함됩니다.

USE HanuriProject;

CREATE TABLE IF NOT EXISTS School (
    school_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    region VARCHAR(100) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 기존 회원의 school_name 들을 가입관리에 자동 등록(노출 ON 으로).
INSERT INTO School (name, is_active)
SELECT DISTINCT u.school_name, TRUE
FROM User u
WHERE u.school_name IS NOT NULL
  AND u.school_name <> ''
  AND NOT EXISTS (
      SELECT 1 FROM School s WHERE s.name = u.school_name
  );
