import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    // Serve index.html for any unknown path so React Router handles it.
    // Without this, reloading /dashboard locally gives a 404 from Vite's dev server.
    historyApiFallback: true,
    proxy: {
      '/api': {
        target: 'https://ml-life-span.onrender.com',
        changeOrigin: true,
      }
    }
  },
  build: {
    outDir: 'dist',
  }
})