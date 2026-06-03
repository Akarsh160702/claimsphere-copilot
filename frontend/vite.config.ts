import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// ClaimSphere Copilot — Vite config
// Proxies /api -> FastAPI backend (default http://localhost:8000) in dev,
// so the frontend talks to the real ClaimSphere API with no CORS friction.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_BACKEND_ORIGIN || "http://localhost:8000",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ""),
      },
    },
  },
});
