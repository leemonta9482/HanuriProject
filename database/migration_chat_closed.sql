-- 기존 DB: 채팅방 종료(대화 끊기) + 동일 글에 새 채팅 허용을 위해 UNIQUE 제거
USE HanuriProject;

ALTER TABLE ChatRoom
  ADD COLUMN closed_at TIMESTAMP NULL DEFAULT NULL AFTER last_message_at;

ALTER TABLE ChatRoom DROP INDEX uniq_listing_initiator;

CREATE INDEX idx_chat_listing_initiator ON ChatRoom (listing_kind, listing_id, initiator_id);
