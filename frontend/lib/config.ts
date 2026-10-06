// URL the BROWSER uses to reach the FastAPI backend (see NEXT_PUBLIC_API_URL in .env).
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export const API_V1 = `${API_BASE_URL}/api/v1`;
