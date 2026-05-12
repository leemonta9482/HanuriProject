# Hanuri 프론트엔드

## 셋업

`frontend` 폴더에서 작업합니다.

### 1. Node.js

`package.json`의 `engines`에 맞는 버전을 사용합니다.

- **Node** `^20.19.0` 또는 `>=22.12.0`

```bash
node -v
npm -v
```

### 2. 의존성 설치

```bash
cd frontend
npm install
```

### 3. 환경 변수

- **운영 빌드**: `frontend/.env.production` (저장소에 커밋하지 않음). 예시는 `.env.production.example` 참고.
- **로컬 개발만** 할 때: `.env.development`에 `VITE_API_BASE_URL` 등 (선택).

Cloudflare 등 **HTTPS 도메인**으로 서비스할 때는 API도 같은 도메인으로 가야 하므로, 빌드 시 예:

```dotenv
VITE_API_BASE_URL=https://예시도메인.shop
```

`src/api/client.ts`의 `getBaseUrl()`이 API 베이스 URL을 결정합니다.

---

## 실행 방법

### 운영용: 빌드 후 정적 프리뷰 (포트 80)

백엔드가 `127.0.0.1:8000`에서 떠 있다는 전제에서, 빌드 산출물을 **127.0.0.1:80**에서 제공합니다. (관리자 권한이 필요할 수 있습니다.)

```bash
cd frontend
npm install
npm run build
npm run preview -- --host 127.0.0.1 --port 80
```

- `npm run build`: 타입 검사(`vue-tsc`) 후 `dist/`에 정적 파일 생성.
- `preview`: `dist`를 서빙합니다. `--host 127.0.0.1 --port 80`은 Cloudflare Tunnel `ingress`에서 프론트를 `http://127.0.0.1:80`으로 넘길 때와 맞추기 위한 값입니다.

브라우저에서 `http://127.0.0.1/` 로 접속해 동작을 확인할 수 있습니다.

### 개발 서버 (로컬 UI 작업 시)

```bash
cd frontend
npm run dev
```

기본은 **포트 5173**(`vite.config.ts`의 `server`). API는 같은 PC에서 보통 **8000**으로 맞춥니다. 필요 시 `.env.development`의 `VITE_API_BASE_URL`을 조정합니다.

---

## 시스템 구성 (개요)

### 역할

**Vue 3** SPA로, Hanuri 백엔드 API와 통신합니다.

### 주요 기술

| 구분 | 내용 |
|------|------|
| 런타임·빌드 | Vite 7, TypeScript |
| UI | Vue 3 (Composition API, SFC) |
| 라우팅 | Vue Router |
| 상태 | Pinia |
| API 호출 | `fetch` 기반 (`src/api/`) |

### 디렉터리 개요

| 경로 | 설명 |
|------|------|
| `src/App.vue` | 레이아웃·헤더·WebSocket 등 |
| `src/router/index.ts` | 라우트·인증·관리자 가드 |
| `src/views/` | 화면별 뷰 |
| `src/api/` | API 클라이언트 및 `client.ts` |
| `src/stores/` | Pinia 스토어 |
| `public/` | 정적 자산 |

---

## 기능 요약 (가입·관리자)

| 구분 | 내용 |
|------|------|
| 회원가입 | 학교 선택·OCR 학생증 인증 등 |
| 관리자 | `/admin/*` — 회원·학교·게시글·신고 등 |

---

`vite.config.ts`의 `preview` 기본값은 `127.0.0.1:80`에 맞춰 두었습니다. 명령줄에서 `--port`를 바꾸면 그 값이 우선합니다.
