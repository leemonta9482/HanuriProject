/**
 * 개발: VITE_API_BASE_URL이 비어 있으면 **현재 페이지 호스트**에 포트 8000 (예: http://192.168.x.x:5173 → http://192.168.x.x:8000).
 * localhost에서 프론트만 열고 백엔드는 LAN IP에서만 뜨는 경우 `.env.development`에 VITE_API_BASE_URL=http://<본인IP>:8000 로 지정.
 */
export function getBaseUrl(): string {
  const raw = import.meta.env.VITE_API_BASE_URL
  const env = typeof raw === 'string' ? raw.trim() : ''
  if (import.meta.env.PROD) {
    return env
  }
  if (typeof window !== 'undefined') {
    const h = window.location.hostname
    if (env) {
      return env.replace(/\/$/, '')
    }
    return `http://${h}:8000`
  }
  return env || 'http://localhost:8000'
}

/** HTTP API 베이스와 동일 호스트로 WebSocket URL (경로만 `/api/ws`). */
export function getWsUrl(): string {
  const http = getBaseUrl()
  try {
    const u = new URL(http)
    u.protocol = u.protocol === 'https:' ? 'wss:' : 'ws:'
    u.pathname = '/api/ws'
    u.search = ''
    u.hash = ''
    return u.toString().replace(/\/$/, '')
  } catch {
    const base = http.replace(/^http/i, 'ws')
    return `${base.replace(/\/$/, '')}/api/ws`
  }
}

/** fetch가 응답 없이 멈출 때(백엔드 미기동·잘못된 호스트 등) UI가 영구 로딩되는 것을 막습니다. */
export function createFetchAbortSignal(timeoutMs: number): AbortSignal {
  if (typeof AbortSignal !== 'undefined' && typeof AbortSignal.timeout === 'function') {
    return AbortSignal.timeout(timeoutMs)
  }
  const ctrl = new AbortController()
  setTimeout(() => ctrl.abort(), timeoutMs)
  return ctrl.signal
}

function requestHadAuthorization(init?: RequestInit): boolean {
  const h = init?.headers
  if (!h) return false
  if (h instanceof Headers) return h.has('Authorization')
  if (Array.isArray(h)) {
    return h.some(([k]) => String(k).toLowerCase() === 'authorization')
  }
  return Object.keys(h as Record<string, string>).some((k) => k.toLowerCase() === 'authorization')
}

const DEFAULT_SESSION_INVALID_MSG = '다른 곳에서 로그인되어 로그아웃됩니다.'

/** 다른 기기 로그인 등으로 세션이 끊겼을 때 App에서 알림 후 로그아웃 */
export function notifySessionInvalid(message?: string): void {
  if (typeof window === 'undefined') return
  window.dispatchEvent(
    new CustomEvent('hanuri:session-invalid', {
      detail: { message: message?.trim() || DEFAULT_SESSION_INVALID_MSG },
    }),
  )
}

async function readJsonDetailFromResponse(res: Response): Promise<string | undefined> {
  try {
    const data = (await res.clone().json()) as { detail?: unknown }
    if (typeof data.detail === 'string' && data.detail.trim()) return data.detail.trim()
    if (Array.isArray(data.detail)) {
      const s = data.detail.map((d: { msg?: string }) => d.msg ?? '').filter(Boolean).join(' ')
      return s || undefined
    }
  } catch {
    /* ignore */
  }
  return undefined
}

/** Bearer가 붙은 요청이 401이면 세션 무효 이벤트(다른 기기 로그인 등) */
export async function apiFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const res = await fetch(input, init)
  if (res.status === 401 && requestHadAuthorization(init)) {
    const detail = await readJsonDetailFromResponse(res)
    notifySessionInvalid(detail)
  }
  return res
}

export async function parseJsonError(res: Response): Promise<string> {
  try {
    const data = (await res.json()) as { detail?: unknown }
    if (typeof data.detail === 'string') return data.detail
    if (Array.isArray(data.detail)) {
      return data.detail.map((d: { msg?: string }) => d.msg ?? '').filter(Boolean).join(' ')
    }
  } catch {
    /* ignore */
  }
  return `요청 실패 (${res.status})`
}

export function authHeadersJson(): HeadersInit {
  const t = localStorage.getItem('hanuri_token')
  const h: Record<string, string> = { 'Content-Type': 'application/json' }
  if (t) h.Authorization = `Bearer ${t}`
  return h
}

/** Authorization만 (multipart 등 Content-Type 없이) */
export function authHeaders(): HeadersInit {
  const t = localStorage.getItem('hanuri_token')
  const h: Record<string, string> = {}
  if (t) h.Authorization = `Bearer ${t}`
  return h
}

/** DB에 저장된 상대경로 → 브라우저에서 열 수 있는 업로드 URL */
export function uploadsPublicUrl(relativePath: string): string {
  const p = relativePath.replace(/^\/+/, '')
  return `${getBaseUrl()}/uploads/${p}`
}
