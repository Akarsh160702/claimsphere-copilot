import axios, { type AxiosInstance } from "axios";

/**
 * Shared Axios instance. In dev, requests go to `/api/*` which Vite proxies to
 * the FastAPI backend (see vite.config.ts). In production set VITE_BACKEND_ORIGIN
 * to the deployed API origin and these calls hit it directly.
 */
const baseURL = import.meta.env.PROD
  ? `${import.meta.env.VITE_BACKEND_ORIGIN ?? ""}`.replace(/\/$/, "")
  : "/api";

export const apiClient: AxiosInstance = axios.create({
  baseURL,
  timeout: 20000,
  headers: { "Content-Type": "application/json" },
});

export const FORCE_DEMO = import.meta.env.VITE_FORCE_DEMO === "true";

/** True when the backend is reachable and reports healthy. */
export async function probeBackend(): Promise<boolean> {
  if (FORCE_DEMO) return false;
  try {
    const res = await apiClient.get("/health", { timeout: 4000 });
    return res.status === 200;
  } catch {
    return false;
  }
}
