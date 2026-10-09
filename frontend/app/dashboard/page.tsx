"use client";

import { useAuth } from "@/components/auth-provider";
import { RequireAuth } from "@/components/require-auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function DashboardContent() {
  const { user, logout } = useAuth();
  if (!user) return null;

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-6 px-6 py-16">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">Welcome, {user.full_name}</h1>
        <p className="mt-1 text-muted-foreground">Learn More. Watch Less.</p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Your account</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p className="text-sm">
            Signed in as <span className="font-medium">{user.email}</span>.
          </p>
          <p className="text-sm text-muted-foreground">
            Courses and AI features are added in later phases.
          </p>
          <Button variant="outline" onClick={() => logout()} className="self-start">
            Sign out
          </Button>
        </CardContent>
      </Card>
    </main>
  );
}

export default function DashboardPage() {
  return (
    <RequireAuth>
      <DashboardContent />
    </RequireAuth>
  );
}