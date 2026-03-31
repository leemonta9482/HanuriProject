USE HanuriProject;

-- 참가자 각자 목록에서만 삭제(상대 목록은 유지). 둘 다 삭제하면 행·메시지 CASCADE 삭제.
ALTER TABLE ChatRoom
  ADD COLUMN deleted_at_initiator TIMESTAMP NULL DEFAULT NULL,
  ADD COLUMN deleted_at_peer TIMESTAMP NULL DEFAULT NULL;
