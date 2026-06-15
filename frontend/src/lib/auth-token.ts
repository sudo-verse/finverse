/** JWT storage. Kept dependency-free so both the axios client and the auth API
 *  can import it without a circular dependency. */
const TOKEN_KEY = "finverse_token";

export const getToken = (): string | null => localStorage.getItem(TOKEN_KEY);
export const setToken = (token: string): void => localStorage.setItem(TOKEN_KEY, token);
export const clearToken = (): void => localStorage.removeItem(TOKEN_KEY);

/** Fired when the API returns 401 so the AuthProvider can drop the session. */
export const UNAUTHORIZED_EVENT = "auth:unauthorized";
