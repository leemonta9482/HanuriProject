import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  /** 같은 PC의 LAN IP(예: 192.168.x.x)로 외부 접속 가능. 방화벽에서 5173 허용 필요할 수 있음. */
  server: {
    host: true,
    port: 5173,
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})
