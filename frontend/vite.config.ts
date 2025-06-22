import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  base: './',
  plugins: [react()],
  server: {
    proxy: {
      '/report': 'http://localhost:8000',
      '/rag': 'http://localhost:8000',
      '/categories': 'http://localhost:8000',
    },
    allowedHosts: true,
  }
});
