-- 기존 DB에 User.school_name 컬럼 추가
USE HanuriProject;

ALTER TABLE User
ADD COLUMN school_name VARCHAR(100) NOT NULL DEFAULT '' COMMENT '학교명' AFTER name;

-- 기존 데이터는 빈 값으로 들어가므로, 운영에서는 여기서 일괄 업데이트하거나
-- 관리자가 회원정보 수정 화면에서 보완하도록 처리하세요.
