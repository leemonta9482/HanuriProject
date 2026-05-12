# 운영 배포 체크리스트

도메인을 통해 서비스를 외부에 공개하기 전에 점검해야 할 항목 모음입니다. Cloudflare Tunnel 설정 본문은 [`cloudflare-tunnel.md`](./cloudflare-tunnel.md) 참고.

---

## 1. 백엔드 (`backend/`)

- [ ] `backend\.env` 작성 완료 (`.env.example` 기반)
  - [ ] `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
  - [ ] `JWT_SECRET` = 32바이트 이상 무작위 문자열
    - 생성 예: `python -c "import secrets;print(secrets.token_urlsafe(48))"`
  - [ ] `APP_PUBLIC_URL=https://hanuri.example.com` (가입 메일 등 외부 링크에 사용)
  - [ ] `SMTP_*` (회원가입 인증/거절 메일을 쓰는 경우)
- [ ] `main.py`의 CORS 와일드카드를 운영 도메인으로 좁힘 (`allow_origins=["https://hanuri.example.com"]`)
- [ ] DB 스키마 최신화 (`database/main.sql` 또는 `database/migrations/*.sql`)
- [ ] 업로드 디렉터리(`backend/uploads/`) 백업 정책 결정 (별도 디스크/주기적 백업)
- [ ] FastAPI Swagger(`/docs`, `/openapi.json`)를 외부에 노출할지 결정
  - 노출 안 함: `config.yml` 인그레스에서 해당 규칙 제거
  - 노출함: Cloudflare Access로 보호 권장

---

## 2. 프론트엔드 (`frontend/`)

- [ ] `frontend\.env.production` 작성
  - [ ] `VITE_API_BASE_URL=https://hanuri.example.com` (단일 도메인 방식)
- [ ] `npm run build` 성공 (`dist/` 생성)
- [ ] preview 또는 정적 서버에서 빌드 결과 확인 (`npm run preview -- --host 127.0.0.1 --port 4173`)
- [ ] `vite.config.ts`의 `preview.allowedHosts`에 도메인 추가 (preview 사용 시)

---

## 3. Cloudflare / DNS

- [ ] Cloudflare 계정 생성·이메일 인증
- [ ] 사이트(도메인) 추가 → **Free 플랜**
- [ ] Cafe24 도메인 관리에서 네임서버를 Cloudflare 네임서버로 변경
- [ ] Cloudflare 사이트 상태 **Active** 확인
- [ ] `cloudflared tunnel login` → `cert.pem` 발급
- [ ] `cloudflared tunnel create hanuri` → `<UUID>.json` 자격증명 확보
- [ ] `%USERPROFILE%\.cloudflared\config.yml` 작성 + `cloudflared tunnel ingress validate` 통과
- [ ] `cloudflared tunnel route dns hanuri hanuri.example.com` 으로 DNS 매핑
- [ ] Cloudflare 대시보드에서 DNS 레코드가 **Proxied(주황 구름)** 인지 확인

---

## 4. 실행 환경

- [ ] 백엔드: `uvicorn main:app --host 127.0.0.1 --port 8000` 상시 기동
- [ ] 프론트: `npm run preview -- --host 127.0.0.1 --port 4173` 또는 정적 서버 상시 기동
- [ ] 터널: `cloudflared service install` 로 Windows 서비스 등록 → `Get-Service cloudflared` 가 `Running`
- [ ] 부팅 시 자동 기동되는지 PC 재부팅 후 확인

---

## 5. 보안

- [ ] `cert.pem`, `<UUID>.json`, `backend/.env` 가 깃 인덱스/원격 저장소에 노출되지 않음
  - `git status` 결과에 보이지 않는지 확인
  - 실수로 푸시했다면 회수 + JWT 시크릿·DB 비밀번호 회전
- [ ] Cloudflare → **SSL/TLS** 모드: `Full` 이상
- [ ] Cloudflare → **Security**: Bot Fight Mode, 기본 WAF 룰 활성
- [ ] 관리자 페이지(`/admin/*`)는 Cloudflare Zero Trust **Access**로 추가 인증 권장
- [ ] OS 계정 비밀번호·디스크 암호화(BitLocker) — `cloudflared` 자격증명이 평문 파일로 디스크에 있음

---

## 6. 기능 동작 점검 (배포 후)

브라우저에서 직접 또는 시크릿 창으로 새로 가입·로그인하며 확인합니다.

- [ ] `https://hanuri.example.com/` → 홈 피드 로드
- [ ] 회원가입 → 학생증 OCR → 이메일 인증 → 관리자 승인 흐름 정상
- [ ] 회원가입 메일 본문의 링크가 `https://hanuri.example.com/...` 로 표시
- [ ] 로그인 후 글 작성·이미지 업로드 → 이미지가 `https://.../uploads/...`로 표시
- [ ] 두 기기에서 동시에 로그인 → 한 쪽이 자동 로그아웃 안내(세션 무효화)
- [ ] 채팅에서 메시지 전송 → 상대 기기에 **실시간(WebSocket)** 도착
- [ ] 다른 기기에서 같은 계정 로그인 시도 시 보안 정책대로 동작
- [ ] 관리자 페이지(`/admin`) 접근·기능

---

## 7. 운영 중 모니터링

- [ ] Cloudflare 대시보드 → **Analytics & Logs**: 트래픽·에러율 주기 확인
- [ ] `cloudflared` 서비스 로그(이벤트 뷰어 또는 `%USERPROFILE%\.cloudflared\`) 주기 확인
- [ ] `backend/uploads/` 디스크 사용량
- [ ] MySQL 백업 (`mysqldump`) 스케줄링
- [ ] 도메인·SMTP 계정 만료일 캘린더 등록

---

## 8. 롤백/장애 대응

- **터널이 죽었을 때**: `Restart-Service cloudflared`. 그래도 안 되면 `cloudflared tunnel run hanuri` 로 포그라운드 실행 후 로그 확인.
- **잘못된 변경 배포 후 되돌리기**: 프론트는 이전 `dist/` 백업 폴더로 교체, 백엔드는 `git checkout <이전 커밋>` 후 재시작.
- **도메인 자체에 문제가 생긴 경우**: Cafe24 네임서버를 원복하면 Cloudflare를 우회하고 다시 자체 네임서버로 돌릴 수 있습니다(다만 지금 구조에서는 다시 Cloudflare로 와야 외부 접속 가능).
