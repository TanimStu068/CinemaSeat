import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    watch: {
      usePolling: true,
    },
    proxy: {
      '/movies': 'http://api:8000',
      '/showtimes': 'http://api:8000',
      '/seats': 'http://api:8000',
      '/otp': 'http://api:8000',
      '/charge': 'http://api:8000',
      '/booking': 'http://api:8000',
    },
  },
})
