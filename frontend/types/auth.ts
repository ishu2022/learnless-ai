export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
}

export interface Tokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Returned by both POST /auth/register and POST /auth/login
export interface AuthResponse {
  user: User;
  tokens: Tokens;
}

// Returned by POST /auth/refresh (no new refresh token is issued)
export interface AccessTokenResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

// One problem found by backend validation (HTTP 422)
export interface ValidationIssue {
  loc: (string | number)[];
  msg: string;
  type: string;
}