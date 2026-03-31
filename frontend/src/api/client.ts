export function getBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
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

/** DB에 저장된 상대경로 → 브라우저에서 열 수 있는 업로드 URL */
export function uploadsPublicUrl(relativePath: string): string {
  const p = relativePath.replace(/^\/+/, '')
  return `${getBaseUrl()}/uploads/${p}`
}
