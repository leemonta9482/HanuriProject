# hanuri

## 빠른 실행

서버가 이미 설정된 상태에서 아래 명령어를 각각 다른 터미널에서 실행합니다.

```bash
# 1. 백엔드 (포트 8000)
cd backend
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

```bash
# 2. 프론트엔드 (포트 80)
cd frontend
npm run build
npm run preview -- --host 127.0.0.1 --port 80
```

```bash
# 3. Cloudflare 터널
cloudflared tunnel run hanuri
```

---

## 소개

이 프로젝트는 대학별 학생들의 중고물품을 사고팔 수 있는 웹입니다.  
FastAPI 기반의 백엔드와 Vue.js 프론트엔드를 사용합니다.

동일 학교(`school_name`)에 소속된 회원만 서로의 판매·구매 희망 글을 볼 수 있도록 하여, 캠퍼스 단위 중고 거래에 맞춰 설계했습니다.

## 개발 팀

**명지전문대학**

팀장 이우진, 팀원 김도현, 팀원 박수완, 팀원 김현서

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
| `/forgot-password` | 비밀번호 찾기 |
| `/password-reset` | 재설정 링크로 비밀번호 변경 |
| `/legal`, `/legal/:doc` | 약관·정책 전문 |
| `/admin/*` | 관리자(회원·게시글·신고 등) — 관리자 권한 필요 |

헤더의 **검색**은 홈 피드 API의 검색 파라미터와 연동됩니다.

### 메일 속 웹 링크 (`APP_PUBLIC_URL`)

가입 거절 안내·비밀번호 재설정 등 **사용자가 여는 URL의 베이스**는 `backend/.env`의 **`APP_PUBLIC_URL`** 입니다. 운영에서는 실제 서비스 도메인과 맞춥니다.  
Windows 등에서 **OS 환경 변수에 같은 이름이 먼저 있으면** `python-dotenv` 기본 동작상 **`.env` 값이 적용되지 않을 수 있습니다.**

---

## 데이터베이스 개요

스키마 정의는 `database/main.sql`을 참고하세요. 주요 엔티티 예시는 다음과 같습니다.

- **User**: 계정, 학교·학과, 가입 승인·학생증, 프로필 이미지, 관리자 여부 등
- **Board**: 판매글(가격, 설명, 거래 장소, 거래 방식, 판매 상태)
- **WantedPost**: 구매 희망글
- **Favorite**: 찜

---

## 프로젝트 구조

```text
HanuriProject/
├── backend/           # FastAPI 앱 (main.py, routers/, models.py, …)
├── frontend/          # Vue 3 SPA (src/views, src/api, …)
├── database/          # main.sql 등 DB 스크립트
├── docs/              # 운영 가이드 (Cloudflare Tunnel 등)
└── README.md
```

---

## 로컬 실행 안내

### 1. 데이터베이스

1. MySQL에서 `database/main.sql`을 실행해 DB·테이블을 생성합니다.
2. 백엔드 환경 변수: `backend` 폴더에 `.env`를 두거나 기본값을 사용합니다.  
   (`config.py` — `db_host`, `db_port`, `db_user`, `db_password`, `db_name`, `jwt_secret` 등)

### 2. 백엔드

API는 **포트 8000 고정**으로 띄웁니다. 자세한 절차는 `backend/README.md`를 참고합니다.

```bash
cd backend
uv sync
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

API 문서: `http://127.0.0.1:8000/docs`

### 3. 프론트엔드

운영에 가깝게 보려면 **빌드 후** `preview`로 정적 파일을 서빙합니다. (기본 예: **127.0.0.1:80** — Windows에서는 관리자 권한이 필요할 수 있습니다.)

```bash
cd frontend
npm install
npm run build
npm run preview -- --host 127.0.0.1 --port 80
```

UI만 빠르게 수정할 때는 `npm run dev`를 쓸 수 있습니다. 상세는 `frontend/README.md`와 `frontend/src/api/client.ts`를 참고하세요.

---

## 도메인 연결 (Cloudflare Tunnel 요약)

외부에서 `https://구매한도메인` 으로 접속하려면 **Cloudflare Tunnel(`cloudflared`)** 을 쓰는 방식을 기준으로 합니다. 포트포워딩 없이 PC에서 백엔드(8000)·프론트(80 등)로 트래픽을 넘깁니다.

1. **Cloudflare** 가입 후 도메인(예: 카페24에서 구매한 도메인)을 사이트로 추가하고, **네임서버를 Cloudflare로 변경**합니다.
2. PC에 **`cloudflared` 설치** 후 `cloudflared tunnel login` 으로 계정과 연결합니다.
3. **`cloudflared tunnel create <이름>`** 으로 터널을 만들고, `%USERPROFILE%\.cloudflared\config.yml`에 **ingress**를 작성합니다.  
   예: `https://도메인/api/*` → `http://127.0.0.1:8000`, 정적 페이지·SPA 나머지 → `http://127.0.0.1:80` 등.
4. **`cloudflared tunnel route dns <터널이름> 도메인`** 으로 DNS를 터널에 연결하거나, Cloudflare DNS에서 CNAME/터널 레코드를 수동으로 맞춥니다.
5. PC에서 **백엔드·프론트·`cloudflared tunnel run …`** 을 동시에 실행한 뒤 브라우저로 확인합니다.
6. 프론트 빌드 시 **`frontend/.env.production`** 에 `VITE_API_BASE_URL=https://도메인` 처럼 **HTTPS·같은 호스트**를 넣어 Mixed Content를 피합니다. 백엔드 `.env`의 `APP_PUBLIC_URL`도 동일한 공개 URL로 맞춥니다.

단계별 설명·트러블슈팅·`www` 서브도메인은 **`docs/cloudflare-tunnel.md`** 에 정리되어 있습니다.

---

## 라이선스

별도 라이선스 파일이 없다면 팀 내부 규정에 따릅니다.
