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
    
    board_id INT,
    buyer_id VARCHAR(50),
    
    status ENUM('REQUESTED', 'ACCEPTED', 'REJECTED') DEFAULT 'REQUESTED',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (board_id) REFERENCES Board(board_id) ON DELETE CASCADE,
    FOREIGN KEY (buyer_id) REFERENCES User(user_id) ON DELETE CASCADE
);


