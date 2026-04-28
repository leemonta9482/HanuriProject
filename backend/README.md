# Hanuri 백엔드

## 셋업

이 저장소의 `backend`는 **uv**로 의존성과 가상환경을 관리합니다. MySQL 서버가 떠 있고, DB·계정·스키마가 준비되어 있다는 전제입니다.

### 1. UV 설치 (Windows)

PowerShell에서 실행합니다.

```powershell
powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

설치 후 버전을 확인합니다.

```powershell
uv --version
```

### 2. Python 버전

`pyproject.toml`의 `requires-python`에 맞는 버전을 씁니다. 예를 들어 프로젝트가 Python 3.14를 요구하면, 해당 버전이 없을 때 설치한 뒤 이 디렉터리에서 고정합니다.

```powershell
cd backend
uv python install 3.14
uv python pin 3.14
```

### 3. 가상환경·의존성

`backend` 폴더에서 가상환경을 만들고, 선언된 패키지를 맞춥니다.

```powershell
cd backend
uv venv .venv
uv sync
```

`uv sync`는 `pyproject.toml` / `uv.lock` 기준으로 `fastapi[standard]`, SQLAlchemy, PyMySQL, PaddleOCR·PaddlePaddle 등이 설치됩니다. Paddle은 `pyproject.toml`의 `[tool.uv.sources]`에 맞춰 CPU 휠 인덱스를 사용합니다. 패키지 목록은 `uv pip list`로 확인할 수 있습니다.

### 4. 환경 변수·데이터베이스

- **`backend/.env`** — `config.py`가 같은 폴더의 `.env`를 `python-dotenv`로 로드한 뒤 **Pydantic Settings**로 읽습니다. Git에는 커밋하지 마세요(`backend/.gitignore`에 `.env` 포함). 처음에는 `backend/.env.example`을 복사해 `backend/.env`를 만든 뒤 값을 채웁니다.
- **민감 정보(DB 비밀번호, JWT 시크릿, SMTP 비밀번호 등)** 는 코드에 두지 않고 `.env`에만 둡니다. 예시 키:
  - MySQL: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
  - JWT: `JWT_SECRET` (운영에서는 긴 무작위 문자열 권장)
  - SMTP·가입 URL: `SMTP_*`, `APP_PUBLIC_URL` (위 README 「기능 요약」 참고)
- DB 스키마는 저장소 루트의 `database/main.sql`(신규 생성) 또는 기존 DB에는 `database/migrations/2026-04-28_add_school.sql`(학교 테이블 추가 등) 적용으로 맞춥니다.

---

## 실행 방법

가상환경을 활성화한 뒤, **항상 `backend` 디렉터리**에서 서버를 띄웁니다.

### 로컬에서만 접속 (개발)

```powershell
.venv\Scripts\activate
uv run fastapi dev main.py --reload --port 8000
```

브라우저에서 API 문서는 `http://127.0.0.1:8000/docs` , 헬스 체크는 `http://127.0.0.1:8000/` 입니다.

### 같은 네트워크의 다른 기기에서 접속

호스트를 바인딩합니다.

```powershell
.venv\Scripts\activate
uv run fastapi dev main.py --host 0.0.0.0 --reload --port 8000
```

운영 배포 시에는 프로세스 관리·HTTPS·방화벽 등을 별도로 구성합니다.

---

## 시스템 구성 (개요)

### 역할

**FastAPI** 기반 REST API 서버로, 캠퍼스 단위 중고 거래(판매글·구매 희망·채팅·관리자)를 지원합니다. 업로드 파일은 로컬 디렉터리에 저장되고 `/uploads` 경로로 정적 제공됩니다.

### 주요 기술


| 구분    | 내용                                                                                                                                   |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------ |
| 프레임워크 | FastAPI                                                                                                                              |
| DB    | MySQL (연결: SQLAlchemy 2.x + PyMySQL, `utf8mb4`)                                                                                      |
| 설정    | Pydantic Settings, `backend/.env`(DB·JWT·SMTP 등 민감 정보). 예시는 `.env.example`                                                                            |
| 인증    | JWT(Bearer), 비밀번호 bcrypt, `token_version`으로 세션 무효화                                                                                   |
| OCR   | **PaddleOCR**, **PaddlePaddle** (`paddleocr`, `paddlepaddle`), 이미지 처리 **Pillow** — 학생증 이미지에서 텍스트 추출 후 회원가입 시 이름·학교명 일치 검증 (`ocr.py`) |


### 디렉터리·모듈 역할


| 경로                   | 설명                                                                             |
| -------------------- | ------------------------------------------------------------------------------ |
| `main.py`            | 앱 생성, 라우터 마운트, CORS, `/uploads` 정적 마운트, 헬스 `/`                                 |
| `config.py`          | DB·JWT·**SMTP(`.env`의 `SMTP_*` 등)**·업로드 경로 등 환경 설정                                                          |
| `database.py`        | SQLAlchemy 엔진·세션 팩토리, `get_db` 의존성                                             |
| `models.py`          | ORM 엔티티 (`User`, **`School`**, `Board`, `WantedPost`, `Chat` 등)                                      |
| `schemas.py`         | 요청/응답 Pydantic 모델                                                              |
| `deps.py`            | `get_current_user`, `require_admin` 등 공통 의존성                                   |
| `security.py`        | JWT 발급·검증, 비밀번호 해시                                                             |
| `upload_storage.py`  | 학생증·프로필·판매 이미지 저장·삭제 규칙                                                        |
| `email_utils.py`       | SMTP 메일 발송(`send_email`), 가입 거절 안내 메일 문구 빌더 (`build_registration_rejected_email`) |
| `ocr.py`               | PaddleOCR로 학생증 OCR, 이름·학교명·학번 포함 여부 검사 (`routers/auth` 학생증 인증과 연동)            |
| `realtime_events.py` | **WebSocket** 실시간 푸시용 인메모리 연결·대기 큐 (`publish_event` → 사용자별 브로드캐스트, 단일 프로세스 전제) |
| `routers/`           | 도메인별 API (`auth`, `admin`, `boards`, `feed`, `wanted`, `chat`, `ws`)           |


### API 라우터 요약

- **auth** — 회원가입(학교 마스터 등록 학교만 허용, 학생증 OCR로 이름·학교명·학번 검증·동일 학교+학번 중복 차단)·짧은 수명 JWT 검증 토큰·로그인·프로필·비밀번호  
  - `GET /api/auth/schools` — 가입 화면용 학교 목록(노출 활성화 학교만)
- **boards** — 판매글 CRUD, 이미지, 찜, 구매 요청, 신고
- **feed** — 동일 학교 기준 통합 피드(판매+구매 희망), 검색·정렬
- **wanted** — 구매 희망글 CRUD
- **chat** — 글 기준 1:1 채팅방·메시지
- **ws** — 로그인 사용자용 **WebSocket** (`GET /api/ws?token=…`, 찜·채팅 알림 등, `realtime_events`와 연동)
- **admin** — 회원·판매글·신고·**학교(가입관리)** 관리  
  - 회원 `PATCH`: 가입 **거절** 시 거절 안내 메일 발송에 **성공한 경우에만** 해당 사용자 행 삭제(실패 시 `502`, 계정 유지). 계정 상태 **삭제**는 메일 없이 행 삭제. 거절 메일은 `email_utils` + `.env` SMTP 설정 사용.

### 데이터·파일

- 스키마 SQL: `database/main.sql`(전체 초기화 시). 기존 DB에 학교 테이블만 추가할 때는 `database/migrations/2026-04-28_add_school.sql` 참고.
- **`School` 테이블** — 가입 시 선택 가능한 학교 마스터(관리자에서 등록·수정·삭제, `User.school_name`과 문자열로 연결).
- 업로드 기본 경로는 `backend/uploads/` 하위이며, `config.Settings.upload_dir`로 결정됩니다.

---

## 기능 요약 (가입·학교·관리자·메일)

| 구분 | 내용 |
|------|------|
| 학교 마스터 | `School` 엔티티·`GET /api/admin/schools` 등 CRUD, 공개 목록 `GET /api/auth/schools` |
| 회원가입 | 등록·노출된 학교만 선택 가능, OCR로 이름·학교명·학번 일치 검증, 동일 학교+학번 기가입 시 차단 |
| 관리자 회원 | 승인·계정 상태 변경; **거절**은 메일 발송 성공 시에만 DB에서 사용자 삭제; **계정 삭제**는 메일 없이 삭제 |
| 메일 | Gmail 등 SMTP는 `backend/.env`의 `SMTP_*` 설정. 미설정·실패 시 거절 플로우에서 삭제 생략(`502`) |

---

- CORS는 개발 편의상 넓게 열려 있을 수 있으므로, 배포 시 출처 제한을 권장합니다.
- **WebSocket** 연결과 `publish_event` 대기 큐는 DB가 아니라 **메모리**이므로, 다중 워커·다중 서버에서는 Redis 등으로 브로드캐스트를 맞춰야 합니다.

