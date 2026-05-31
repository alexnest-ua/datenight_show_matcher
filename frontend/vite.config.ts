import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In dev, with the default empty VITE_API_BASE, the app calls /health and /api/*
// on the same origin. We proxy those to the FastAPI backend on :8090 so there is
// no CORS dance. SSE (/api/stream) works through the proxy too (ws: false, but
// EventSource is plain HTTP chunked, which the http proxy streams fine).
const BACKEND = "http://localhost:8090";

export default defineConfig({
  plugins: [react()],
  build: {
    // Cloudflare Pages output dir.
    outDir: "dist",
    target: "es2022",
  },
  server: {
    proxy: {
      "/api": {
        target: BACKEND,
        changeOrigin: true,
      },
      "/health": {
        target: BACKEND,
        changeOrigin: true,
      },
    },
  },
});
