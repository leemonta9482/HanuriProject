USE HanuriProject;

CREATE TABLE IF NOT EXISTS ChatRoom (
  room_id INT AUTO_INCREMENT PRIMARY KEY,
  listing_kind ENUM('BOARD','WANTED') NOT NULL,
  listing_id INT NOT NULL,
  initiator_id VARCHAR(50) NOT NULL,
  peer_id VARCHAR(50) NOT NULL,
  last_message_at TIMESTAMP NULL DEFAULT NULL,
  closed_at TIMESTAMP NULL DEFAULT NULL,
  deleted_at_initiator TIMESTAMP NULL DEFAULT NULL,
  deleted_at_peer TIMESTAMP NULL DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_chat_listing_initiator (listing_kind, listing_id, initiator_id),
  INDEX idx_initiator (initiator_id),
  INDEX idx_peer (peer_id),
  FOREIGN KEY (initiator_id) REFERENCES User(user_id) ON DELETE CASCADE,
  FOREIGN KEY (peer_id) REFERENCES User(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ChatMessage (
  message_id INT AUTO_INCREMENT PRIMARY KEY,
  room_id INT NOT NULL,
  sender_id VARCHAR(50) NOT NULL,
  body TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (room_id) REFERENCES ChatRoom(room_id) ON DELETE CASCADE,
  FOREIGN KEY (sender_id) REFERENCES User(user_id) ON DELETE CASCADE,
  INDEX idx_room (room_id, message_id)
);
