-- 프로필 이미지(선택). 기존 DB에 적용 시 한 번만 실행.
ALTER TABLE User
  ADD COLUMN profile_image_path VARCHAR(512) NULL
  AFTER student_id_card_path;
