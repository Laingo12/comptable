import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@': path.resolve(__dirname, './src') } },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
    css: false,
    exclude: ['tests/e2e/**', 'node_modules/**'],
    testTimeout: 20_000,
    hookTimeout: 20_000,
    // Réduit la contention : max 4 workers sur Windows pour stabiliser les durées.
    poolOptions: {
      threads: { maxThreads: 4, minThreads: 1 },
    },
  },
});