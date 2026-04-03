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

`uv sync`는 `pyproject.toml` / `uv.lock` 기준으로 `fastapi[standard]`, SQLAlchemy, PyMySQL 등이 설치됩니다. 패키지 목록은 `uv pip list`로 확인할 수 있습니다.

### 4. 환경 변수·데이터베이스

- `backend`에 `.env`를 두면 `config.py`의 **Pydantic Settings**가 읽습니다. 없으면 코드에 적힌 기본값(로컬 MySQL 등)이 사용됩니다.
- DB 스키마는 저장소 루트의 `database/main.sql` 등을 참고해 생성·적용합니다.

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


| 구분    | 내용                                                      |
| ----- | ------------------------------------------------------- |
| 프레임워크 | FastAPI                                                 |
| DB    | MySQL (연결: SQLAlchemy 2.x + PyMySQL, `utf8mb4`)         |
| 설정    | Pydantic Settings, `backend/.env` (없으면 `config.py` 기본값) |
| 인증    | JWT(Bearer), 비밀번호 bcrypt, `token_version`으로 세션 무효화      |


### 디렉터리·모듈 역할


| 경로                   | 설명                                                                       |
| -------------------- | ------------------------------------------------------------------------ |
| `main.py`            | 앱 생성, 라우터 마운트, CORS, `/uploads` 정적 마운트, 헬스 `/`                           |
| `config.py`          | DB·JWT·업로드 경로 등 환경 설정                                                    |
| `database.py`        | SQLAlchemy 엔진·세션 팩토리, `get_db` 의존성                                       |
| `models.py`          | ORM 엔티티 (User, Board, WantedPost, Chat 등)                                |
| `schemas.py`         | 요청/응답 Pydantic 모델                                                        |
| `deps.py`            | `get_current_user`, `require_admin` 등 공통 의존성                             |
| `security.py`        | JWT 발급·검증, 비밀번호 해시                                                       |
| `upload_storage.py`  | 학생증·프로필·판매 이미지 저장·삭제 규칙                                                  |
| `realtime_events.py` | SSE용 **인메모리** 구독 큐 (프로세스 단일 인스턴스 전제)                                     |
| `routers/`           | 도메인별 API (`auth`, `admin`, `boards`, `feed`, `wanted`, `chat`, `events`) |


### API 라우터 요약

- **auth** — 회원가입·로그인·프로필·비밀번호
- **boards** — 판매글 CRUD, 이미지, 찜, 구매 요청, 신고
- **feed** — 동일 학교 기준 통합 피드(판매+구매 희망), 검색·정렬
- **wanted** — 구매 희망글 CRUD
- **chat** — 글 기준 1:1 채팅방·메시지
- **events** — 로그인 사용자용 **SSE** 스트림 (`realtime_events`와 연동)
- **admin** — 회원·판매글·신고 관리

### 데이터·파일

- 스키마 SQL 예시는 저장소 루트의 `database/main.sql` 등을 참고하면 됩니다.
- 업로드 기본 경로는 `backend/uploads/` 하위이며, `config.Settings.upload_dir`로 결정됩니다.

### 운영 시 참고

- CORS는 개발 편의상 넓게 열려 있을 수 있으므로, 배포 시 출처 제한을 권장합니다.
- SSE 이벤트 큐는 DB가 아니라 **메모리**이므로, 다중 워커·다중 서버에서는 브로드캐스트 방식을 별도로 두어야 합니다.

