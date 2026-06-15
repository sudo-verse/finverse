import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import * as authApi from "@/api/auth";
import { UNAUTHORIZED_EVENT, clearToken, getToken, setToken } from "@/lib/auth-token";

interface AuthContextValue {
  user: authApi.AuthUser | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<authApi.AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let active = true;

    // A 401 anywhere (axios or SSE) ends the session.
    const onUnauthorized = () => setUser(null);
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized);

    if (getToken()) {
      authApi
        .fetchMe()
        .then((u) => active && setUser(u))
        .catch(() => clearToken())
        .finally(() => active && setIsLoading(false));
    } else {
      setIsLoading(false);
    }

    return () => {
      active = false;
      window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
    };
  }, []);

  const login = async (email: string, password: string) => {
    const res = await authApi.login(email, password);
    setToken(res.accessToken);
    setUser(res.user);
  };

  const register = async (email: string, password: string, fullName?: string) => {
    const res = await authApi.register(email, password, fullName);
    setToken(res.accessToken);
    setUser(res.user);
  };

  const logout = () => {
    clearToken();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
