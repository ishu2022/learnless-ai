"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchReadiness } from "@/lib/api";

export function useHealth() {
  return useQuery({
    queryKey: ["health", "ready"],
    queryFn: fetchReadiness,
    refetchInterval: 10_000,
    retry: false,
  });
}
