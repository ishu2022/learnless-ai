"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

// Shown on /login and /register when you are already signed in.
export function RedirectToDashboard() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/dashboard");
  }, [router]);

  return <p className="text-sm text-muted-foreground">Redirecting…</p>;
}