/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<object, object, unknown>
  export default component
}

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  /** VITE_API_BASE_URL 이 없을 때만 사용. 기본 8000 */
  readonly VITE_API_BACKEND_PORT?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
