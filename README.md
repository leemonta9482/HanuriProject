# hanuri

## 소개

이 프로젝트는 대학별 학생들의 중고물품을 사고팔 수 있는 웹입니다.  
FastAPI 기반의 백엔드와 Vue.js 프론트엔드를 사용합니다.

동일 학교(`school_name`)에 소속된 회원만 서로의 판매·구매 희망 글을 볼 수 있도록 하여, 캠퍼스 단위 중고 거래에 맞춰 설계했습니다.

## 개발자

**명지전문대학**

이우진, 김도현, 박수완, 김현서

---

## 기술 스택

| 구분 | 사용 기술 |
|------|-----------|
| 프론트엔드 | Vue 3, TypeScript, Vite, Vue Router, Pinia |
| 백엔드 | FastAPI, SQLAlchemy, Pydantic Settings |
| 데이터베이스 | MySQL (utf8mb4) |
| 인증 | JWT (Bearer), 비밀번호 해시(bcrypt) |
| 파일 | 서버 로컬 `uploads/` 정적 제공 (`/uploads`) |

---

## 시스템 구성

```text
[브라우저]  →  Vue SPA (Vite)
                  ↓ REST API (/api/...)
              FastAPI
                  ↓
              MySQL  ←  SQLAlchemy ORM
```

- **API**: `/api` 하위에 인증(`auth`), 피드(`feed`), 판매글(`boards`), 구매 희망(`wanted`), 채팅(`chat`), 관리자(`admin`), 실시간 이벤트(`events`) 등 라우터가 분리되어 있습니다.
- **정적 파일**: 게시글·프로필 등 이미지는 백엔드 `uploads` 디렉터리에 저장되고 `/uploads/...` URL로 제공됩니다.
- **CORS**: 개발 편의를 위해 백엔드에서 CORS가 열려 있습니다. 운영 배포 시에는 허용 출처를 제한하는 것을 권장합니다.

---

## 사이트 구성 (주요 화면)

| 경로 | 설명 |
|------|------|
| `/` | 홈: 학교 단위 통합 피드(판매글 + 구매 희망), 정렬·검색(제목·설명·장소·작성자 학과 등) |
| `/write` | 글 작성(판매 / 구매 희망 선택) — 로그인 필요 |
| `/boards/:id` | 판매글 상세, 찜, 채팅(구매 문의), 신고, 판매자 상점 이동 |
| `/boards/:id/edit` | 판매글 수정 |
| `/wanted/:id` | 구매 희망글 상세 |
| `/favorites` | 찜한 판매글 |
| `/my-shop` | 내 상점(내 판매글 목록·상태 변경·삭제) |
| `/shop/:userId` | 다른 사용자 상점 |
| `/profile` | 프로필·비밀번호 수정 |
| `/chat` | 채팅 목록·대화 |
| `/login`, `/register` | 로그인·회원가입 |
| `/admin/*` | 관리자(회원·게시글·신고 등) — 관리자 권한 필요 |

헤더의 **검색**은 홈 피드 API의 검색 파라미터와 연동됩니다.

---

## 데이터베이스 개요

스키마 정의는 `database/main.sql`을 참고하세요. 주요 엔티티 예시는 다음과 같습니다.

- **User**: 계정, 학교·학과, 가입 승인·학생증, 프로필 이미지, 관리자 여부 등
- **Board**: 판매글(가격, 설명, 거래 장소, 거래 방식, 판매 상태)
- **WantedPost**: 구매 희망글
- **Favorite**: 찜
- **PurchaseRequest** 등: 구매 요청·거래 흐름 관련 테이블

---

## 프로젝트 구조

```text
HanuriProject/
├── backend/           # FastAPI 앱 (main.py, routers/, models.py, …)
├── frontend/          # Vue 3 SPA (src/views, src/api, …)
├── database/          # main.sql 등 DB 스크립트
└── README.md
```

---

## 로컬 실행 안내

### 1. 데이터베이스

1. MySQL에서 `database/main.sql`을 실행해 DB·테이블을 생성합니다.
2. 백엔드 환경 변수: `backend` 폴더에 `.env`를 두거나 기본값을 사용합니다.  
   (`config.py` — `db_host`, `db_port`, `db_user`, `db_password`, `db_name`, `jwt_secret` 등)

### 2. 백엔드

```bash
cd backend
# 의존성 설치 (uv 예시)
uv sync
# 또는 pip / 가상환경에 맞게 설치
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API 문서: 브라우저에서 `http://127.0.0.1:8000/docs` (FastAPI Swagger)

### 3. 프론트엔드

```bash
cd frontend
npm install
npm run dev
```

Vite 기본 주소는 보통 `http://127.0.0.1:5173` 입니다.  
API 베이스 URL은 `frontend/src/api/client.ts` 등 프로젝트 설정을 확인하세요.

---

## 라이선스

별도 라이선스 파일이 없다면 팀 내부 규정에 따릅니다.
