-- 기존 DB에 마켓플레이스 테이블/제약을 추가할 때 사용합니다.
-- 이미 main.sql로 처음부터 만든 경우 이 파일은 필요 없습니다.

USE HanuriProject;

-- PurchaseRequest에 (board_id, buyer_id) 유니크가 없을 때만 실행 (에러 나면 스킵)
-- ALTER TABLE PurchaseRequest ADD UNIQUE KEY uniq_board_buyer (board_id, buyer_id);

CREATE TABLE IF NOT EXISTS BoardImage (
    image_id INT AUTO_INCREMENT PRIMARY KEY,
    board_id INT NOT NULL,
    path VARCHAR(512) NOT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    FOREIGN KEY (board_id) REFERENCES Board(board_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Report (
    report_id INT AUTO_INCREMENT PRIMARY KEY,
    board_id INT NOT NULL,
    reporter_id VARCHAR(50) NOT NULL,
    reason VARCHAR(2000) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_report_board_user (board_id, reporter_id),
    FOREIGN KEY (board_id) REFERENCES Board(board_id) ON DELETE CASCADE,
    FOREIGN KEY (reporter_id) REFERENCES User(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS WantedPost (
    wanted_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    max_price INT,
    preferred_location VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);
