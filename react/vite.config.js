import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'


// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      // Proxy API requests to the backend server
      '/api': {
        target: 'http://localhost:80',
        changeOrigin: true,
      },
      // Proxy auth-related requests
      '/accounts': {
        target: 'http://localhost:80',
        changeOrigin: true,
      },
      '/auth': {
        target: 'http://localhost:80',
        changeOrigin: true,
      },
    }
  }
})
