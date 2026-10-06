"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useHealth } from "@/hooks/use-health";
import { API_BASE_URL } from "@/lib/config";

const LABELS: Record<string, string> = {
  database: "PostgreSQL + pgvector",
  redis: "Redis",
  storage: "MinIO object storage",
};

export function ServiceStatus() {
  const { data, error, isLoading, isFetching, refetch } = useHealth();

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle>System status</CardTitle>
          <p className="text-sm text-muted-foreground">
            {data ? `${data.service} v${data.version} · ${data.environment}` : "Checking the backend…"}
          </p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="rounded-md border border-border px-3 py-1.5 text-sm font-medium hover:bg-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary disabled:opacity-60"
        >
          {isFetching ? "Checking…" : "Check again"}
        </button>
      </CardHeader>
      <CardContent>
        {isLoading && <p className="text-sm text-muted-foreground">Loading…</p>}

        {error && (
          <div role="alert" className="rounded-md bg-destructive/10 p-4 text-sm text-destructive">
            <p className="font-medium">Can&apos;t reach the backend at {API_BASE_URL}.</p>
            <p className="mt-1">
              Make sure the stack is running with <code>docker compose up --build</code>, then check
              again.
            </p>
          </div>
        )}

        {data && (
          <ul className="divide-y divide-border">
            <li className="flex items-center justify-between py-3">
              <span className="font-medium">Backend API</span>
              <Badge variant="success">Running</Badge>
            </li>
            {Object.entries(data.components).map(([key, c]) => (
              <li key={key} className="flex items-center justify-between gap-4 py-3">
                <div>
                  <span className="font-medium">{LABELS[key] ?? key}</span>
                  <p className="text-sm text-muted-foreground">
                    {c.detail ?? "Connected"}
                    {c.latency_ms !== null && ` · ${c.latency_ms} ms`}
                  </p>
                </div>
                <Badge variant={c.status === "ok" ? "success" : "destructive"}>
                  {c.status === "ok" ? "Connected" : "Down"}
                </Badge>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
