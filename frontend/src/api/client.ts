import axios from "axios";

import { UNAUTHORIZED_EVENT, clearToken, getToken } from "@/lib/auth-token";

/** In dev, /api is proxied to the FastAPI backend (see vite.config.ts).
 *  In production set VITE_API_URL to the deployed API base. */
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "/api",
  timeout: 60_000, // report generation (Gemini) can take tens of seconds
  headers: { "Content-Type": "application/json" },
});

// Attach the bearer token to every request when signed in.
apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// On 401, drop the session so the app redirects to /login — but not for the
// login/register calls themselves (a wrong password shouldn't log you out).
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const url: string = error.config?.url ?? "";
    const isAuthCall = url.includes("/auth/login") || url.includes("/auth/register");
    if (error.response?.status === 401 && !isAuthCall) {
      clearToken();
      window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
    }
    return Promise.reject(error);
  },
);
