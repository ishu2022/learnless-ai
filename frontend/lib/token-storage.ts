// The ONLY place that touches browser storage.
// We store just the refresh token. The access token lives in memory only.
const REFRESH_TOKEN_KEY = "learnless.refresh_token";

export function getStoredRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(REFRESH_TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setStoredRefreshToken(token: string): void {
  try {
    window.localStorage.setItem(REFRESH_TOKEN_KEY, token);
  } catch {
    // Storage can be blocked (private mode, full). The user just won't stay logged in.
  }
}

export function clearStoredRefreshToken(): void {
  try {
    window.localStorage.removeItem(REFRESH_TOKEN_KEY);
  } catch {
    // Nothing to clear if storage is unavailable.
  }
}