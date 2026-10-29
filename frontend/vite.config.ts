import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  // "/" for local dev; "/<repo-name>/" when hosted on GitHub Pages (set by the deploy workflow).
  const raw = env.VITE_BASE_PATH || '/';
  const base = `/${raw.replace(/^\/+|\/+$/g, '')}/`.replace(/^\/\/$/, '/');

  return {
    base,
    plugins: [react()],
    server: {
      port: 5173,
      host: 'localhost',
    },
    preview: {
      port: 4173,
    },
  };
});
