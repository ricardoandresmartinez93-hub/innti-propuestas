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
        // Innti realiza hasta 8 llamadas secuenciales × 30 s/llamada = ~240 s máx.
        // El timeout debe superar ese valor con margen.
        timeout: 360_000,
        proxyTimeout: 360_000,
      },
    },
  },
})
