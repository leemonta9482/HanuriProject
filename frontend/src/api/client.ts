/**
 * API 베이스 URL
 * - Cloudflare Tunnel: 브라우저는 **`https://mtaoft.shop/api/...`** 만 호출해야 함. `http://…:8000`은 Mixed Content 차단.
 * - 인터넷에서 `http://mtaoft.shop:8000` 은 **공인으로 8000이 열려 있지 않아** 접속 불가가 정상(8000은 PC의 127.0.0.1에만 바인딩).
 * - `.env.production`에는 `VITE_API_BASE_URL=https://mtaoft.shop` 권장(또는 비워 두면 HTTPS 공인 호스트에서는 `origin` 사용).
 */
function sameSiteApexOrWww(a: string, b: string): boolean {
  const x = a.toLowerCase()
  const y = b.toLowerCase()
  if (x === y) return true
  const strip = (h: string) => (h.startsWith('www.') ? h.slice(4) : h)
  return strip(x) === strip(y)
}

/** HTTPS 페이지에서 같은 사이트로 `http://도메인:포트` 를 쓰면 브라우저가 막음 → `https://현재호스트` 로 통일 */
function coerceApiBaseForHttpsPage(base: string): string {
  if (typeof window === 'undefined' || window.location.protocol !== 'https:') {
    return base
  }
  const pageHost = window.location.hostname
  const pageLoop =
    pageHost === 'localhost' ||
    pageHost === '127.0.0.1' ||
    pageHost === '[::1]' ||
    pageHost === '::1'
  if (pageLoop) return base

  let u: URL
  try {
    u = new URL(base)
  } catch {
    return base
  }
  if (u.protocol !== 'http:') return base
  if (sameSiteApexOrWww(u.hostname, pageHost)) {
    return window.location.origin
  }
  return base
}

function computeApiBaseUrl(): string {
  const raw = import.meta.env.VITE_API_BASE_URL
  const env = typeof raw === 'string' ? raw.trim() : ''

  const portRaw = import.meta.env.VITE_API_BACKEND_PORT
  const backendPort =
    typeof portRaw === 'string' && /^\d+$/.test(portRaw.trim()) ? portRaw.trim() : '8000'

  if (env) {
    const cleaned = env.replace(/\/$/, '')
    try {
      const hasScheme = /^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//.test(cleaned)
      const u = new URL(hasScheme ? cleaned : `http://${cleaned}`)
      const noExplicitPort = u.port === ''
      const loopback =
        u.hostname === 'localhost' ||
        u.hostname === '127.0.0.1' ||
        u.hostname === '[::1]'
      if (u.protocol === 'http:' && loopback && noExplicitPort) {
        const h = u.hostname === '[::1]' ? '127.0.0.1' : u.hostname
        return `http://${h}:${backendPort}`
      }
      const resolved = hasScheme ? cleaned : `${u.protocol}//${u.host}`.replace(/\/$/, '')
      if (
        typeof window !== 'undefined' &&
        window.location.protocol === 'https:' &&
        u.protocol === 'http:' &&
        sameSiteApexOrWww(u.hostname, window.location.hostname)
      ) {
        return window.location.origin
      }
      return resolved
    } catch {
      return cleaned
    }
  }

  if (typeof window !== 'undefined') {
    if (window.location.protocol === 'https:') {
      const loopback =
        window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1' ||
        window.location.hostname === '[::1]'
      if (!loopback) {
        return window.location.origin
      }
    }
    const h = window.location.hostname
    const host = h === '::1' || h === '[::1]' ? '127.0.0.1' : h
    return `http://${host}:${backendPort}`
  }
  return `http://localhost:${backendPort}`
}

export function getBaseUrl(): string {
  return coerceApiBaseForHttpsPage(computeApiBaseUrl())
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
