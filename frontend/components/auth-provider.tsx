"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  ApiError,
  fetchCurrentUser,
  loginUser,
  logoutUser,
  refreshAccessToken,
  registerUser,
} from "@/lib/api";
import {
  clearStoredRefreshToken,
  getStoredRefreshToken,
  setStoredRefreshToken,
} from "@/lib/token-storage";
import type { AuthResponse, LoginPayload, RegisterPayload, User } from "@/types/auth";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  user: User | null;
  accessToken: string | null;
  status: AuthStatus;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");

  // On page load: turn a stored refresh token back into a logged-in session.
  useEffect(() => {
    let cancelled = false;

    async function restoreSession() {
      const refreshToken = getStoredRefreshToken();
      if (!refreshToken) {
        setStatus("unauthenticated");
        return;
      }
      try {
        const { access_token } = await refreshAccessToken(refreshToken);
        const currentUser = await fetchCurrentUser(access_token);
        if (cancelled) return;
        setUser(currentUser);
        setAccessToken(access_token);
        setStatus("authenticated");
      } catch (error) {
        if (cancelled) return;
        // Only a 401 means the token is truly bad. A network error or server
        // problem must not wipe a token that may still be valid.
        if (error instanceof ApiError && error.status === 401) {
          clearStoredRefreshToken();
        }
        setStatus("unauthenticated");
      }
    }

    restoreSession();
    return () => {
      cancelled = true;
    };
  }, []);

  const startSession = useCallback((data: AuthResponse) => {
    setStoredRefreshToken(data.tokens.refresh_token);
    setUser(data.user);
    setAccessToken(data.tokens.access_token);
    setStatus("authenticated");
  }, []);

  const login = useCallback(
    async (payload: LoginPayload) => {
      startSession(await loginUser(payload));
    },
    [startSession],
  );

  const register = useCallback(
    async (payload: RegisterPayload) => {
      startSession(await registerUser(payload));
    },
    [startSession],
  );

  const logout = useCallback(async () => {
    const refreshToken = getStoredRefreshToken();
    if (refreshToken) {
      try {
        await logoutUser(refreshToken);
      } catch {
        // Even if the server can't be reached, still log out locally.
      }
    }
    clearStoredRefreshToken();
    setUser(null);
    setAccessToken(null);
    setStatus("unauthenticated");
  }, []);

  const value = useMemo(
    () => ({ user, accessToken, status, login, register, logout }),
    [user, accessToken, status, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error("useAuth must be used inside <AuthProvider>");
  }
  return context;
}