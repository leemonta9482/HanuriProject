# Hanuri 운영 문서

이 폴더에는 한우리(Hanuri) 서비스를 외부에 노출하기 위한 운영 가이드를 모아 둡니다.

## 문서 목록

| 문서 | 내용 |
|------|------|
| [`cloudflare-tunnel.md`](./cloudflare-tunnel.md) | Cloudflare Tunnel + Cafe24 도메인으로 서비스를 인터넷에 공개하는 전체 절차 |
| [`production-checklist.md`](./production-checklist.md) | 도메인 공개 전후로 점검해야 할 운영 체크리스트 (CORS, 환경 변수, 빌드, 보안) |

## 빠른 요약

```text
[인터넷 사용자]
       │  https://hanuri.example.com
       ▼
 [Cloudflare Edge]   ← TLS/HTTPS 종단, DDoS·캐시
       │  암호화된 아웃바운드 터널
       ▼
 [내 PC: cloudflared]
       │
       ├── /api/*       → http://127.0.0.1:8000  (FastAPI)
       ├── /uploads/*   → http://127.0.0.1:8000  (정적 업로드)
       ├── /api/ws      → http://127.0.0.1:8000  (WebSocket)
       └── /            → http://127.0.0.1:4173  (Vue 빌드 결과 preview)
```

- 도메인은 **Cafe24**에서 구매했지만 DNS 운영은 **Cloudflare**로 위임합니다(네임서버 변경).
- 공유기 포트포워딩, 공인 IP, 인바운드 방화벽 개방이 **필요 없습니다**. `cloudflared`가 아웃바운드로만 연결합니다.
- 도메인 한 개로 프론트·백엔드·WebSocket을 **경로 기반 라우팅**으로 모두 노출합니다.

자세한 절차는 [`cloudflare-tunnel.md`](./cloudflare-tunnel.md)를 참고하세요.
