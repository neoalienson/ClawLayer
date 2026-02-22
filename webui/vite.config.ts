import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:11435',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true
  }
});
