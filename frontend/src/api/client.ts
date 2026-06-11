import axios from "axios";

/** In dev, /api is proxied to the FastAPI backend (see vite.config.ts).
 *  In production set VITE_API_URL to the deployed API base. */
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "/api",
  timeout: 60_000, // report generation (Gemini) can take tens of seconds
  headers: { "Content-Type": "application/json" },
});
