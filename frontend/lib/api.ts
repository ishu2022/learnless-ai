import { API_V1 } from "@/lib/config";
import type {
  AccessTokenResponse,
  AuthResponse,
  LoginPayload,
  RegisterPayload,
  User,
} from "@/types/auth";
import type { ReadinessResponse } from "@/types/health";

/**
 * GET /health/ready answers 200 when every dependency is up and 503 when one is down.
 * Both carry the same JSON body, so both are valid results for the status page.
 */
export async function fetchReadiness(): Promise<ReadinessResponse> {
  const res = await fetch(`${API_V1}/health/ready`, { cache: "no-store" });
  if (res.status === 200 || res.status === 503) {
    return (await res.json()) as ReadinessResponse;
  }
  throw new Error(`Backend returned HTTP ${res.status}`);
}

/**
 * Error thrown for any failed backend call.
 * status 0 means the request never reached the server (backend down, network issue).
 * The backend always answers errors as {"error": {"code", "message", "details"}}.
 */
export class ApiError extends Error {
  status: number;
  code: string;
  details: unknown;

  constructor(status: number, code: string, message: string, details: unknown = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

interface RequestOptions {
  method?: "GET" | "POST";
  body?: unknown;
  accessToken?: string;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, accessToken } = options;

  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;

  let res: Response;
  try {
    res = await fetch(`${API_V1}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      cache: "no-store",
    });
  } catch {
    throw new ApiError(0, "network_error", "Could not reach the server. Please try again.");
  }

  if (!res.ok) {
    let code = `http_${res.status}`;
    let message = `Request failed (HTTP ${res.status})`;
    let details: unknown = null;
    try {
      const data = await res.json();
      if (data?.error) {
        code = data.error.code ?? code;
        message = data.error.message ?? message;
        details = data.error.details ?? null;
      }
    } catch {
      // Response had no JSON body; keep the generic message above.
    }
    throw new ApiError(res.status, code, message, details);
  }

  // 204 No Content (logout) has no body to parse.
  if (res.status === 204) return undefined as T;

  return (await res.json()) as T;
}

export function registerUser(payload: RegisterPayload): Promise<AuthResponse> {
  return request<AuthResponse>("/auth/register", { method: "POST", body: payload });
}

export function loginUser(payload: LoginPayload): Promise<AuthResponse> {
  return request<AuthResponse>("/auth/login", { method: "POST", body: payload });
}

export function refreshAccessToken(refreshToken: string): Promise<AccessTokenResponse> {
  return request<AccessTokenResponse>("/auth/refresh", {
    method: "POST",
    body: { refresh_token: refreshToken },
  });
}

export function logoutUser(refreshToken: string): Promise<void> {
  return request<void>("/auth/logout", {
    method: "POST",
    body: { refresh_token: refreshToken },
  });
}

export function fetchCurrentUser(accessToken: string): Promise<User> {
  return request<User>("/auth/me", { accessToken });
}