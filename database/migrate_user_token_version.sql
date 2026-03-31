-- 기존 DB에 적용: 한 번만 실행
USE HanuriProject;

ALTER TABLE User
  ADD COLUMN token_version INT NOT NULL DEFAULT 0 AFTER is_admin;
