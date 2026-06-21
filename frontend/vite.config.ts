import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://localhost:8001',
    },
  },
  define: {
    // Fallback to empty string (uses relative /api proxy in dev)
    __API_BASE__: JSON.stringify(process.env.VITE_API_URL ?? ''),
  },
})
