import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  /** 프론트 80 → 메일 등 `http://localhost/password-reset` 과 포트 일치. LAN·방화벽·Windows 관리자 권한 이슈 가능. */
  server: {
    host: true,
    port: 80,
    strictPort: true,
  },
  /** Cloudflare Tunnel 등으로 외부 도메인 Host로 preview에 접속할 때 필요 */
  preview: {
    host: '127.0.0.1',
    port: 80,
    strictPort: true,
    allowedHosts: ['mtaoft.shop', 'www.mtaoft.shop'],
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})
