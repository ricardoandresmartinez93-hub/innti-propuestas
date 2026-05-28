import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

/**
 * Vitest configuration (separate from vite.config.ts so the build config
 * is not polluted with test-only settings).
 */
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    // Apply the global setup before every test file
    setupFiles: ['./src/test-setup.ts'],
    // Default environment for all test files (overridable per-file with
    // the @vitest-environment docblock comment)
    environment: 'jsdom',
  },
})
