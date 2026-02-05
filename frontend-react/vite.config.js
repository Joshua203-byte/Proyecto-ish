import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
      '/uploads': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
// Trigger rebuild mié 04 feb 2026 19:17:33 CST
// Force rebuild mié 04 feb 2026 19:26:05 CST
// Force rebuild jue 05 feb 2026 08:10:39 CST
