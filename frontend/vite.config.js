import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const API = process.env.VITE_API_PROXY || 'http://localhost:8000'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': API,
      '/media': API,
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.js'],
    restoreMocks: true,
  },
})
