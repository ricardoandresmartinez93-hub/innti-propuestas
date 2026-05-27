import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // Timeout generoso para endpoints de generación de documentos
        // que pueden tardar varios segundos (python-docx + conversión PDF).
        timeout: 120_000,
        proxyTimeout: 120_000,
      },
    },
  },
})
