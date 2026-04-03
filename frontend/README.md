# Hanuri 프론트엔드

## 셋업

이 저장소에는 이미 `frontend` 앱이 포함되어 있습니다. 아래는 **이 폴더에서 개발할 때**의 절차입니다.

### 1. Node.js

`package.json`의 `engines`에 맞는 버전을 사용합니다.

- **Node** `^20.19.0` 또는 `>=22.12.0`

설치 후 확인합니다.

```bash
node -v
npm -v
```

### 2. 의존성 설치

프로젝트 루트가 아니라 **`frontend` 디렉터리**에서 실행합니다.

```bash
cd frontend
npm install
```

### 3. 환경 변수 (선택)

백엔드 주소를 고정하려면 `frontend`에 `.env.development` 등을 두고 `VITE_API_BASE_URL`을 설정합니다. 자세한 동작은 아래 **API 베이스 URL**을 참고합니다.

### 참고: 처음부터 Vue 프로젝트를 만들 때

새 저장소를 만들 때만 해당합니다. 공식 스캐폴드는 다음과 같습니다.

```bash
npm create vue@latest
```

TypeScript·Vue Router·Pinia를 켜고, Vitest·ESLint 등은 팀 정책에 맞게 선택하면 됩니다. Hanuri 본 저장소는 이미 위 옵션에 가깝게 구성되어 있으므로, **일반적으로는 `npm install`만 하면 됩니다.**

---

## 실행 방법

역시 **`frontend` 폴더**에서 실행합니다.

### 개발 서버

```bash
cd frontend
npm run dev
```

기본적으로 Vite는 **포트 5173**에서 뜨며, `vite.config.ts`의 `server.host: true` 설정으로 LAN에서 접속할 수 있습니다. 터미널에 표시되는 URL(예: `http://127.0.0.1:5173`)을 브라우저에서 엽니다.

백엔드는 보통 **포트 8000**에서 실행한다는 전제이며, 같은 PC에서는 별도 설정 없이도 API 호스트가 맞춰지는 경우가 많습니다. 틀리면 `.env.development`의 `VITE_API_BASE_URL`을 조정합니다.

### 빌드·프리뷰

```bash
npm run build
npm run preview
```

`build`는 타입 검사(`vue-tsc`)와 번들을 포함합니다. 운영 배포 시에는 빌드 산출물과 `VITE_*` 환경 변수를 호스팅 환경에 맞게 넣습니다.

---

## 시스템 구성 (개요)

### 역할

**Vue 3** 단일 페이지 애플리케이션(SPA)으로, Hanuri 백엔드 API와 통신해 캠퍼스 중고 거래(피드·글 작성·채팅·프로필·관리자 화면 등)를 제공합니다.

### 주요 기술

| 구분 | 내용 |
|------|------|
| 런타임·빌드 | Vite 7, TypeScript |
| UI | Vue 3 (Composition API, SFC) |
| 라우팅 | Vue Router |
| 상태 | Pinia (`stores/`, 예: 인증 토큰·사용자 정보) |
| API 호출 | `fetch` 기반 래퍼 (`src/api/`) |

### 디렉터리 개요

| 경로 | 설명 |
|------|------|
| `src/App.vue` | 레이아웃·헤더(로고·검색·네비·드롭다운)·전역 알림·SSE 등 |
| `src/main.ts` | 앱 부트스트랩, Pinia·Router 연결 |
| `src/router/index.ts` | 경로·`meta.requiresAuth` / `requiresAdmin` 가드 |
| `src/views/` | 화면별 뷰(홈, 글 작성·상세, 채팅, 로그인, 관리자 등) |
| `src/api/` | 엔드포인트별 클라이언트(`auth`, `boards`, `feed`, `chat` …) 및 공통 `client.ts` |
| `src/stores/` | Pinia 스토어 |
| `src/assets/` | 전역 스타일 등 |
| `public/` | 정적 자산(파비콘 등) |

### API 베이스 URL (개발)

`src/api/client.ts`의 `getBaseUrl()`이 백엔드 주소를 결정합니다. 개발 모드에서는 기본적으로 **현재 접속 호스트 + 포트 8000**(예: `http://127.0.0.1:8000`)을 쓰고, 필요 시 `.env.development`의 `VITE_API_BASE_URL`로 덮어쓸 수 있습니다. 운영 빌드에서는 `VITE_API_BASE_URL` 등 환경 변수 설정이 필요합니다.

### 개발 서버 (참고)

`vite.config.ts`에서 개발 서버는 **호스트 `true`**, **포트 5173**으로 설정되어 있어 LAN IP로 접속해 테스트할 수 있습니다. 백엔드 CORS·방화벽 설정은 환경에 맞게 맞춥니다.
