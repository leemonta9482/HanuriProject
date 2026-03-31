-- 기존 Report 테이블에 관리자 검토 컬럼 추가 (이미 main.sql로 만든 DB는 스킵)
USE HanuriProject;

ALTER TABLE Report
  ADD COLUMN status ENUM('PENDING', 'REVIEWED', 'DISMISSED', 'ACTION_TAKEN') NOT NULL DEFAULT 'PENDING' AFTER reason,
  ADD COLUMN reviewed_at TIMESTAMP NULL DEFAULT NULL AFTER status,
  ADD COLUMN reviewed_by VARCHAR(50) NULL AFTER reviewed_at,
  ADD COLUMN admin_note VARCHAR(2000) NULL AFTER reviewed_by;

ALTER TABLE Report
  ADD CONSTRAINT fk_report_reviewed_by FOREIGN KEY (reviewed_by) REFERENCES User(user_id) ON DELETE SET NULL;
