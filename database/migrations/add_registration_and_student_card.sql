-- 기존 DB에 가입 승인 상태·학생증 경로 컬럼 추가
USE HanuriProject;

ALTER TABLE User
ADD COLUMN registration_status ENUM('PENDING', 'APPROVED', 'REJECTED') NOT NULL DEFAULT 'APPROVED'
  COMMENT '가입 승인 상태' AFTER is_admin;

ALTER TABLE User
ADD COLUMN student_id_card_path VARCHAR(512) NOT NULL DEFAULT ''
  COMMENT '학생증 이미지 경로' AFTER registration_status;

-- 기존 행은 이미 승인된 것으로 두고, 학생증 경로가 비어 있으면 더미 값(추후 관리자가 교체 가능)
UPDATE User SET student_id_card_path = CONCAT('_legacy/', user_id) WHERE student_id_card_path = '';
