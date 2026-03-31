CREATE DATABASE HanuriProject
CHARACTER SET utf8mb4
COLLATE utf8mb4_general_ci;

USE HanuriProject;

-- 유저 테이블
CREATE TABLE User (
    user_id VARCHAR(50) PRIMARY KEY,         -- 아이디 (PK)
    password VARCHAR(255) NOT NULL,          -- 비밀번호 (암호화 저장)
    name VARCHAR(50) NOT NULL,               -- 이름
    school_name VARCHAR(100) NOT NULL,       -- 학교명
    phone VARCHAR(20) UNIQUE NOT NULL,       -- 전화번호 (중복 방지)
    email VARCHAR(100) UNIQUE NOT NULL,      -- 이메일 (중복 방지)
    
    student_id VARCHAR(20),                  -- 학번
    student_verified BOOLEAN DEFAULT FALSE,  -- 학생 인증 여부
    
    manner_score FLOAT DEFAULT 36.5,         -- 매너온도 (당근마켓 방식)
    trust_score FLOAT DEFAULT 0,             -- 신뢰점수
    
    interest_major VARCHAR(100),             -- 관심 전공
    
    account_status ENUM('ACTIVE', 'DORMANT', 'DELETED') DEFAULT 'ACTIVE',
    
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,   -- 관리자 여부

    token_version INT NOT NULL DEFAULT 0,      -- 로그인 시마다 증가, JWT tv와 매칭(다른 곳 로그인 시 이전 세션 무효)
    
    registration_status ENUM('PENDING', 'APPROVED', 'REJECTED') NOT NULL DEFAULT 'PENDING',  -- 가입 승인 상태
    student_id_card_path VARCHAR(512) NOT NULL,   -- 학생증 이미지 저장 경로(서버 기준 상대경로)
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 게시판 테이블
CREATE TABLE Board (
    board_id INT AUTO_INCREMENT PRIMARY KEY,   -- 게시글 번호 (PK)
    
    user_id VARCHAR(50) NOT NULL,              -- 작성자
    
    title VARCHAR(200) NOT NULL,               -- 상품명
    price INT NOT NULL,                        -- 가격
    description TEXT,                          -- 설명
    
    location VARCHAR(255),                     -- 거래 장소
    
    trade_type ENUM('DIRECT', 'DELIVERY', 'BOTH') DEFAULT 'BOTH',
    
    status ENUM('ON_SALE', 'RESERVED', 'SOLD') DEFAULT 'ON_SALE',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES User(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- 좋아요 테이블
CREATE TABLE Favorite (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50),
    board_id INT,
    
    UNIQUE(user_id, board_id),
    
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (board_id) REFERENCES Board(board_id) ON DELETE CASCADE
);

-- 구매요청 테이블
CREATE TABLE PurchaseRequest (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    board_id INT NOT NULL,
    buyer_id VARCHAR(50) NOT NULL,
    
    status ENUM('REQUESTED', 'ACCEPTED', 'REJECTED') DEFAULT 'REQUESTED',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uniq_board_buyer (board_id, buyer_id),
    
    FOREIGN KEY (board_id) REFERENCES Board(board_id) ON DELETE CASCADE,
    FOREIGN KEY (buyer_id) REFERENCES User(user_id) ON DELETE CASCADE
);

-- 판매글 이미지 (여러 장)
CREATE TABLE BoardImage (
    image_id INT AUTO_INCREMENT PRIMARY KEY,
    board_id INT NOT NULL,
    path VARCHAR(512) NOT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    FOREIGN KEY (board_id) REFERENCES Board(board_id) ON DELETE CASCADE
);

-- 게시글 신고
CREATE TABLE Report (
    report_id INT AUTO_INCREMENT PRIMARY KEY,
    board_id INT NOT NULL,
    reporter_id VARCHAR(50) NOT NULL,
    reason VARCHAR(2000) NOT NULL,
    status ENUM('PENDING', 'REVIEWED', 'DISMISSED', 'ACTION_TAKEN') NOT NULL DEFAULT 'PENDING',
    reviewed_at TIMESTAMP NULL DEFAULT NULL,
    reviewed_by VARCHAR(50) NULL,
    admin_note VARCHAR(2000) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_report_board_user (board_id, reporter_id),
    FOREIGN KEY (board_id) REFERENCES Board(board_id) ON DELETE CASCADE,
    FOREIGN KEY (reporter_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES User(user_id) ON DELETE SET NULL
);

-- 구매 희망글 (원하는 상품 등록)
CREATE TABLE WantedPost (
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

-- 거래 채팅 (판매글·구매 희망글별 1:1, initiator가 대화 시작한 쪽, 종료 시 closed_at 설정)
CREATE TABLE ChatRoom (
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
    FOREIGN KEY (initiator_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (peer_id) REFERENCES User(user_id) ON DELETE CASCADE
);

CREATE TABLE ChatMessage (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    sender_id VARCHAR(50) NOT NULL,
    body TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES ChatRoom(room_id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES User(user_id) ON DELETE CASCADE
);