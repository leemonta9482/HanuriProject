# Cloudflare Tunnel + Cafe24 도메인 연결 가이드

이 문서는 **Cafe24에서 구매한 도메인**을 사용해, **Cloudflare Tunnel(cloudflared)** 로 한우리(Hanuri) 서비스를 인터넷에 공개하는 전체 절차입니다. 공인 IP, 포트포워딩, 인바운드 방화벽 개방이 필요 없습니다.

> 예시 도메인은 `example.com`으로 적습니다. 실제 본인 도메인으로 바꿔 읽으세요.

---

## 0. 사전 이해

### 왜 Cloudflare Tunnel인가

- **포트포워딩 불필요**: 내 PC에서 Cloudflare로 **아웃바운드** 연결만 합니다. 공유기·ISP 환경(공인 IP 없음, 통신사 NAT 등)에서도 동작합니다.
- **HTTPS 자동**: Cloudflare 엣지가 TLS 인증서를 자동 발급·갱신합니다. 내부 서버는 `http://127.0.0.1:포트`로 평문 통신해도 인터넷 구간은 HTTPS입니다.
- **무료 플랜으로 충분**: Cloudflare Free 플랜 + cloudflared(오픈소스)로 운영 가능합니다. (Zero Trust도 무료 등급이 있습니다.)
- **WebSocket·대용량 업로드 지원**: `wss://`, 멀티파트 업로드 모두 그대로 통과합니다.

### 최종 구조

```text
사용자 브라우저 ── HTTPS ──▶ Cloudflare Edge
                                │
                                │ 암호화된 아웃바운드 터널 (QUIC/HTTPS)
                                ▼
                         내 PC: cloudflared
                                │
                  ┌─────────────┼──────────────────────────┐
                  ▼             ▼                          ▼
        http://127.0.0.1:80   http://127.0.0.1:8000     http://127.0.0.1:8000
        (Vue 빌드: 정적)         (/api/*, /uploads/*)       (/api/ws WebSocket)
```

- `**hanuri.example.com**` 하나로 전부 노출하고, `cloudflared`의 인그레스(ingress) 규칙으로 경로별 라우팅합니다.
- 서브도메인 분리(`api.example.com`)도 가능합니다(부록 참고).

---

## 1. Cloudflare 가입

1. [https://dash.cloudflare.com/sign-up](https://dash.cloudflare.com/sign-up) 에서 이메일·비밀번호로 가입합니다.
2. 메일함에 도착한 **이메일 인증 메일**의 링크를 클릭해 계정을 활성화합니다.
3. 로그인 후 대시보드([https://dash.cloudflare.com](https://dash.cloudflare.com))에 들어갑니다.

> 결제 정보 등록은 필요 없습니다(Free 플랜 사용).

---

## 2. Cloudflare에 도메인 추가 (사이트 등록)

1. 대시보드 좌측 메뉴에서 **Websites** → **Add a site (사이트 추가)** 클릭.
2. Cafe24에서 구매한 도메인(예: `example.com`)을 입력하고 계속.
3. 플랜 선택 화면에서 **Free**를 선택.
4. Cloudflare가 기존 DNS 레코드를 자동 스캔합니다. 빈 상태일 가능성이 높으니 그대로 진행.
5. 마지막 단계에서 Cloudflare가 **두 개의 네임서버**(예시)
  ```
   alice.ns.cloudflare.com
   bob.ns.cloudflare.com
  ```
   를 보여줍니다. **이 값을 그대로 복사**해 둡니다(Cafe24에 등록할 값).

> 이 단계에서는 아직 DNS가 활성화되지 않습니다. Cafe24에서 네임서버를 바꿔야 Cloudflare가 "Active"로 표시됩니다.

---

## 3. Cafe24에서 네임서버 변경

1. Cafe24 도메인 관리 페이지([https://hosting.cafe24.com/?controller=user_main](https://hosting.cafe24.com/?controller=user_main)) 로그인.
2. 상단 **나의 서비스 관리** → **도메인 관리** → 해당 도메인의 **관리** 클릭.
3. 좌측 또는 상단 메뉴에서 **네임서버 변경** (또는 "네임서버 정보 변경") 선택.
4. 1차/2차 네임서버 입력란을 **Cloudflare가 알려준 두 개의 네임서버**로 교체합니다.
  - 1차: `alice.ns.cloudflare.com`
  - 2차: `bob.ns.cloudflare.com`
5. 변경 사항 저장.
6. 적용까지 **수 분 ~ 최대 24~48시간**이 소요됩니다(보통 10~30분 안에 됨).

### 네임서버 적용 확인

PowerShell에서:

```powershell
nslookup -type=NS example.com
```

응답에 Cloudflare 네임서버 두 개가 나오면 적용 완료입니다. Cloudflare 대시보드의 사이트도 **Active** 배지로 바뀌고, 등록한 메일로 **"Your domain is active"** 메일이 옵니다.

> 적용이 완료되기 전에 다음 단계로 진행해도 됩니다. DNS 레코드는 미리 만들어 둘 수 있습니다.

---

## 4. cloudflared 설치 (Windows)

서비스를 실행할 PC(여기서는 개발용 PC)에 `cloudflared`를 설치합니다.

### 방법 A: 공식 설치 파일 (권장)

1. [https://github.com/cloudflare/cloudflared/releases/latest](https://github.com/cloudflare/cloudflared/releases/latest) 에서
  `cloudflared-windows-amd64.msi` 다운로드.
2. 더블 클릭으로 설치. 기본 경로는 `C:\Program Files (x86)\cloudflared\`.
3. PowerShell **새 창**을 열고 버전 확인:
  ```powershell
   cloudflared --version
  ```
   `cloudflared version 20xx.xx.x` 와 같이 나오면 OK.

### 방법 B: winget

```powershell
winget install --id Cloudflare.cloudflared
```

---

## 5. cloudflared 인증

브라우저 로그인으로 cloudflared를 내 Cloudflare 계정과 연결합니다.

```powershell
cloudflared tunnel login
```

- 출력에 표시되는 URL이 자동으로 브라우저에서 열립니다.
- Cloudflare 로그인 후, 인증할 도메인(`example.com`)을 선택 → **Authorize**.
- 성공하면 `%USERPROFILE%\.cloudflared\cert.pem` 파일이 생성됩니다. 이 파일이 인증 토큰입니다.

> `cert.pem`은 **외부에 유출하지 마세요**. 깃에 커밋하지 않습니다.

---

## 6. 터널 생성

원하는 이름(여기서는 `hanuri`)으로 터널을 만듭니다.

```powershell
cloudflared tunnel create hanuri
```

성공 출력 예:

```
Tunnel credentials written to C:\Users\Monta\.cloudflared\<UUID>.json.
Created tunnel hanuri with id <UUID>
```

- `<UUID>`(예: `12345678-aaaa-bbbb-cccc-ddddeeeeffff`)와 자격증명 JSON 경로를 메모해 둡니다.
- 자격증명 JSON 파일(`<UUID>.json`)은 **이 터널을 실행할 수 있는 비밀키**입니다. 절대 커밋하지 마세요.

### 터널 목록 확인

```powershell
cloudflared tunnel list
```

---

## 7. 백엔드/프론트엔드 준비

도메인 노출에 앞서 실제로 외부에서 접속했을 때 정상 동작하도록 준비합니다.

### 7-1. 백엔드 (FastAPI)

`backend\.env`에 운영용 값을 채웁니다(중요 항목만 발췌):

```dotenv
# 외부에서 가입 메일 등에 사용할 공개 URL
APP_PUBLIC_URL=https://hanuri.example.com

# JWT 비밀(긴 무작위 문자열)
JWT_SECRET=<32바이트 이상 무작위 문자열>

# DB 등 기존 값 그대로
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=...
DB_PASSWORD=...
DB_NAME=...
```

서버 실행은 **루프백(127.0.0.1)** 으로만 열어도 충분합니다(외부 노출은 cloudflared가 담당):

```powershell
cd backend
.venv\Scripts\activate
uv run uvicorn main:app --host 127.0.0.1 --port 8000
```

> `--host 0.0.0.0`도 가능하지만, Cloudflare Tunnel을 쓰는 한 굳이 LAN에 열 필요는 없습니다.

### 7-2. 프론트엔드 (Vue + Vite)

운영에서는 `vite dev` 대신 **빌드된 정적 파일**을 사용합니다.

`frontend\.env.production` 생성:

```dotenv
VITE_API_BASE_URL=https://hanuri.example.com
```

> 프론트엔드의 `getBaseUrl()`(`frontend/src/api/client.ts`)이 `import.meta.env.PROD`에서 이 값을 그대로 사용합니다. 그래서 도메인 하나로 묶었을 때 API/업로드/WebSocket이 모두 동일 호스트로 호출됩니다.

빌드:

```powershell
cd frontend
npm install
npm run build
```

빌드 결과는 `frontend\dist\`에 생깁니다. 이걸 서비스할 정적 서버가 필요해요. 가장 쉬운 방법은 Vite의 preview 서버를 그대로 쓰는 것입니다:

```powershell
npm run preview -- --host 127.0.0.1 --port 4173
```

- `127.0.0.1:4173`에서 정적 파일을 제공합니다.
- 더 견고하게 운영하려면 `serve`, `nginx`, `caddy` 같은 전용 정적 서버를 써도 됩니다.

### 7-3. CORS 정리(선택)

도메인 한 개로 묶으면 브라우저 입장에서 동일 출처라 CORS 자체가 필요 없습니다. 그래도 운영에서는 `backend\main.py`의 와일드카드 CORS를 좁히는 걸 권장합니다.

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://hanuri.example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 8. 터널 설정 파일(`config.yml`) 작성

`cloudflared`가 어떤 호스트로 들어온 요청을 내부의 어떤 포트로 보낼지 정의합니다.

경로: `**%USERPROFILE%\.cloudflared\config.yml**` (예: `C:\Users\Monta\.cloudflared\config.yml`)

```yaml
tunnel: <UUID>
credentials-file: C:\Users\Monta\.cloudflared\<UUID>.json

ingress:
  # 1) API
  - hostname: hanuri.example.com
    path: ^/api/.*
    service: http://127.0.0.1:8000

  # 2) 업로드 정적 파일
  - hostname: hanuri.example.com
    path: ^/uploads/.*
    service: http://127.0.0.1:8000

  # 3) FastAPI Swagger(원하면 노출, 운영에서 닫고 싶으면 이 블록 제거)
  - hostname: hanuri.example.com
    path: ^/docs$
    service: http://127.0.0.1:8000
  - hostname: hanuri.example.com
    path: ^/openapi.json$
    service: http://127.0.0.1:8000

  # 4) 그 외 전부 프론트엔드 정적
  - hostname: hanuri.example.com
    service: http://127.0.0.1:4173

  # 5) 마지막은 반드시 catch-all
  - service: http_status:404
```

포인트:

- `path`는 **정규식**입니다. `^/api/.`*는 `/api/...`로 시작하는 모든 경로.
- `/api/ws` WebSocket도 `^/api/.*` 규칙으로 자동 처리됩니다(별도 설정 불필요).
- 규칙은 **위에서 아래로** 평가되므로, 더 구체적인 규칙을 위에 둡니다.
- 마지막 `service: http_status:404`(catch-all)는 **필수**입니다.

### 설정 검증

```powershell
cloudflared tunnel ingress validate
```

`Validating rules from C:\Users\Monta\.cloudflared\config.yml ... OK` 가 나오면 됩니다.

특정 URL이 어떤 규칙에 매칭되는지 시뮬레이션:

```powershell
cloudflared tunnel ingress rule https://hanuri.example.com/api/feed
cloudflared tunnel ingress rule https://hanuri.example.com/uploads/x.jpg
cloudflared tunnel ingress rule https://hanuri.example.com/
```

---

## 9. DNS 레코드 연결

터널을 도메인에 묶습니다(Cloudflare DNS에 CNAME이 자동 등록됩니다).

```powershell
cloudflared tunnel route dns hanuri hanuri.example.com
```

루트 도메인(`example.com`)을 그대로 쓰고 싶다면:

```powershell
cloudflared tunnel route dns hanuri example.com
```

Cloudflare 대시보드 → 사이트 → **DNS → Records**에 들어가면 해당 호스트가 **Proxied(주황 구름)** 상태로 등록된 것을 확인할 수 있습니다.

> 이미 같은 이름의 레코드가 있으면 명령이 실패할 수 있어요. 대시보드에서 기존 A/AAAA/CNAME 레코드를 지운 뒤 다시 실행합니다.

---

## 10. 터널 실행

### 10-1. 일단 임시로 띄워서 동작 확인

```powershell
cloudflared tunnel run hanuri
```

다른 터미널에서 백엔드(8000)와 프론트엔드 preview(4173)가 떠 있어야 합니다.
이제 브라우저에서:

- `https://hanuri.example.com/` → Vue 화면
- `https://hanuri.example.com/api/auth/schools` → JSON 응답
- `https://hanuri.example.com/api/ws?token=...` → WebSocket(웹앱이 자동으로 연결)

이 모두 정상이면 OK. Ctrl+C로 종료.

### 10-2. Windows 서비스로 등록 (자동 시작·재시작)

운영에서는 부팅 시 자동 실행되도록 서비스로 등록합니다. **관리자 권한 PowerShell**에서:

```powershell
cloudflared service install
```

> `config.yml`과 `<UUID>.json`이 `%USERPROFILE%\.cloudflared\`에 있어야 합니다. 서비스 컨텍스트에서도 같은 경로를 참조하도록 `cloudflared`가 자동 복사·등록합니다.

서비스 상태 확인:

```powershell
Get-Service cloudflared
```

수동 시작/중지:

```powershell
Start-Service cloudflared
Stop-Service cloudflared
Restart-Service cloudflared
```

로그(서비스 모드):

- `C:\Windows\System32\config\systemprofile\.cloudflared\` 또는
- 이벤트 뷰어 → Windows 로그 → 응용 프로그램(원본: `cloudflared`)

---

## 11. 검증 체크리스트


| 항목                    | 확인 방법                                                  |
| --------------------- | ------------------------------------------------------ |
| 네임서버 변경 적용            | `nslookup -type=NS example.com` 응답에 Cloudflare NS      |
| Cloudflare 사이트 Active | 대시보드의 사이트 상태 배지                                        |
| 터널 정상                 | `cloudflared tunnel list` 에서 `CONNECTIONS` 열에 4개 활성 연결 |
| 프론트 접속                | `https://hanuri.example.com/` 로 Vue SPA 로드             |
| API 접속                | `https://hanuri.example.com/api/auth/schools` JSON 응답  |
| 업로드 이미지               | 게시글에서 이미지 정상 표시(주소가 `https://...uploads/...`)          |
| WebSocket             | 로그인 후 다른 기기에서 메시지/찜 알림 즉시 수신                           |
| HTTPS 인증서             | 브라우저 자물쇠 아이콘에 Cloudflare 인증서                           |


---

## 12. 트러블슈팅

### "Bad Gateway 502" 가 뜬다

- 백엔드(8000) 또는 프론트 preview(4173)가 안 떠 있는 경우. 로컬에서 `http://127.0.0.1:8000/`, `http://127.0.0.1:4173/`이 열리는지 먼저 확인.

### Vite preview에서 "Blocked request. This host is not allowed."

- `frontend\vite.config.ts`의 `preview` 블록에 도메인을 허용 추가:
  ```ts
  export default defineConfig({
    // ...
    preview: {
      host: '127.0.0.1',
      port: 4173,
      allowedHosts: ['hanuri.example.com'],
    },
  })
  ```

### 개발 모드(`vite dev`)를 그대로 노출해야 하는 경우

- 같은 방식으로 `server.allowedHosts: ['hanuri.example.com']` 를 추가하고, `config.yml`의 `/` 라우팅을 `http://127.0.0.1:5173`로 바꿉니다. **운영용은 빌드된 정적이 더 안전합니다.**

### 회원가입 이메일 안의 링크가 `http://127.0.0.1...`로 나간다

- `backend\.env`의 `APP_PUBLIC_URL`을 `https://hanuri.example.com` 으로 설정했는지 확인 후 서버 재시작.

### WebSocket이 끊긴다

- Cloudflare는 기본적으로 약 100초 idle 후 끊을 수 있습니다. 클라이언트가 자동 재연결되도록 짠 상태라면 문제 없어요(현재 코드 기준 재연결 로직이 있다면 그대로). 필요하면 Cloudflare 대시보드 → **Network**에서 WebSocket이 켜져 있는지 확인.

### "tunnel credentials file not found"

- 서비스 모드에서 `config.yml`의 `credentials-file` 경로를 잘못 적은 경우. 절대경로(`C:\Users\Monta\.cloudflared\<UUID>.json`)로 적으세요.

### DNS는 떴는데 `Error 1033` 등이 보인다

- 터널이 안 떠 있어서 그렇습니다. `Get-Service cloudflared`로 상태 확인, 또는 `cloudflared tunnel run hanuri`로 직접 실행하여 로그 확인.

---

## 13. 보안 권장사항

- `cert.pem`, `<UUID>.json`, `backend/.env`는 **절대 깃에 커밋하지 않기**(이미 `.gitignore`에 `.env`는 포함됨).
- `JWT_SECRET`은 충분히 긴 무작위 문자열(예: `python -c "import secrets;print(secrets.token_urlsafe(48))"`).
- CORS는 운영에서 와일드카드 대신 자신의 도메인으로 좁히기.
- FastAPI `/docs`(Swagger) 노출이 불필요하면 `config.yml`에서 해당 규칙 제거.
- Cloudflare 대시보드 → **SSL/TLS** → 암호화 모드는 **Full** 또는 **Full (strict)** 가 아니라, 터널을 쓰는 경우 **Flexible** 대신 기본값(보통 **Full**)으로 두면 됩니다(터널 구간은 Cloudflare가 자체 암호화).
- Cloudflare → **Security → Bots / WAF**에서 기본 Bot Fight Mode, 기본 WAF 룰을 켜두면 좋습니다(무료).
- 관리 화면(`/admin` 등)은 Cloudflare Zero Trust **Access**로 추가 인증(이메일·OTP)을 거는 것을 권장합니다(부록 참고).

---

## 14. 부록 A. 서브도메인 분리 방식

도메인 한 개로 묶는 게 싫고, API를 따로 두고 싶다면:

- `hanuri.example.com` → 프론트
- `api.hanuri.example.com` → 백엔드

`config.yml`:

```yaml
tunnel: <UUID>
credentials-file: C:\Users\Monta\.cloudflared\<UUID>.json

ingress:
  - hostname: api.hanuri.example.com
    service: http://127.0.0.1:8000
  - hostname: hanuri.example.com
    service: http://127.0.0.1:4173
  - service: http_status:404
```

DNS 추가:

```powershell
cloudflared tunnel route dns hanuri hanuri.example.com
cloudflared tunnel route dns hanuri api.hanuri.example.com
```

이 경우 프론트의 `.env.production`:

```dotenv
VITE_API_BASE_URL=https://api.hanuri.example.com
```

그리고 백엔드 CORS에 `https://hanuri.example.com`을 명시적으로 허용해야 합니다.

---

## 15. 부록 B. 관리자 페이지 보호 (Cloudflare Access)

운영 도메인의 `/admin/*`은 외부에서 누구나 접근할 수 있는 상태입니다. Cloudflare Zero Trust **Access**로 이메일 OTP/구글 SSO 같은 보호 계층을 무료로 추가할 수 있어요.

1. Cloudflare 대시보드 → 좌측 **Zero Trust** 진입(처음이면 팀 이름 설정).
2. **Access → Applications → Add an application → Self-hosted**.
3. Application name: `Hanuri Admin`, Domain: `hanuri.example.com`, Path: `/admin`*.
4. Identity provider는 기본 **One-time PIN(이메일)** 사용 가능.
5. Policy에 본인·운영자 이메일만 **Allow**.

이렇게 하면 `/admin` 진입 시 Cloudflare가 먼저 이메일 OTP를 요구한 뒤 통과시킵니다.

---

## 16. 운영 흐름 요약 (치트시트)

```powershell
# 1) DB·백엔드 기동
cd backend
.venv\Scripts\activate
uv run uvicorn main:app --host 127.0.0.1 --port 8000

# 2) 프론트엔드 빌드 + preview
cd ..\frontend
npm run build
npm run preview -- --host 127.0.0.1 --port 4173

# 3) 터널 (서비스로 등록 안 했을 때만)
cloudflared tunnel run hanuri
```

서비스로 등록했다면 1)·2)만 켜두면 됩니다. 부팅 시 자동 기동을 원하면 백엔드·프론트도 `nssm`이나 작업 스케줄러로 서비스화하는 것을 권장합니다(별도 운영 작업).

---

문서에 더 필요한 항목(예: 백엔드·프론트 자체를 Windows 서비스로 등록하는 법, nginx로 정적 호스팅하기, GitHub Actions로 자동 배포)이 있으면 추가로 정리해 둘 수 있습니다.