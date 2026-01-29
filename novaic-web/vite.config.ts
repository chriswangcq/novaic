import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  
  server: {
    port: 3000,
    // Proxy API requests to Gateway during development
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:19999',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://127.0.0.1:19999',
        ws: true,
      },
    },
  },
  
  // Env variables
  envPrefix: ['VITE_'],
  
  build: {
    // Support top-level await (noVNC needs it)
    target: 'esnext',
    minify: 'esbuild',
    sourcemap: process.env.NODE_ENV !== 'production',
    // Output to dist for deployment
    outDir: 'dist',
  },
  
  optimizeDeps: {
    esbuildOptions: {
      target: 'esnext',
    },
  },
  
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      // Use src/lib for noVNC ESM sources
      'novnc-rfb': path.resolve(__dirname, './src/lib/novnc/rfb.js'),
    },
  },
});
