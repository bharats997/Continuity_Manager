import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3001, // Frontend dev server port
    proxy: {
      // Proxy API requests to the backend
      '/api': {
        target: 'http://localhost:8000', // Your backend API URL
        changeOrigin: true,
        // If your backend API routes don't start with /api, you might need a rewrite rule
        // rewrite: (path) => path.replace(/^\/api/, '') 
      }
    }
  }
})
