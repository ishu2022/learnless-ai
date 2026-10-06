export type ComponentStatus = "ok" | "error";

export interface ComponentHealth {
  status: ComponentStatus;
  latency_ms: number | null;
  detail: string | null;
}

export interface ReadinessResponse {
  status: "ok" | "degraded";
  service: string;
  version: string;
  environment: string;
  components: Record<string, ComponentHealth>;
}
