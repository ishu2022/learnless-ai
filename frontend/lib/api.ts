import { API_V1 } from "@/lib/config";
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
