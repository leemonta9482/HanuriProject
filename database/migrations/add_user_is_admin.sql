-- 기존 HanuriProject DB에 User.is_admin 컬럼 추가 (이미 적용된 경우 생략)
USE HanuriProject;

ALTER TABLE User
ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE COMMENT '관리자 여부' AFTER account_status;
