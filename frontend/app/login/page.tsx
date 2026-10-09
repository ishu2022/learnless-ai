"use client";

import Link from "next/link";
import { useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { RedirectToDashboard } from "@/components/redirect-to-dashboard";import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api";
import { fieldErrorsFrom } from "@/lib/form-errors";

function LoginForm() {
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setFormError(null);
    setFieldErrors({});

    try {
      await login({ email: email.trim(), password });
    } catch (error) {
      if (error instanceof ApiError) {
        const fields = fieldErrorsFrom(error);
        if (Object.keys(fields).length > 0) {
          setFieldErrors(fields);
        } else {
          setFormError(error.message);
        }
      } else {
        setFormError("Something went wrong. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      {formError && (
        <div role="alert" className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
          {formError}
        </div>
      )}

      <FormField id="email" label="Email" error={fieldErrors.email}>
        <Input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={submitting}
        />
      </FormField>

      <FormField id="password" label="Password" error={fieldErrors.password}>
        <Input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={submitting}
        />
      </FormField>

      <Button type="submit" disabled={submitting}>
        {submitting ? "Signing in…" : "Sign in"}
      </Button>
    </form>
  );
}

export default function LoginPage() {
  const { status } = useAuth();

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-6 px-6 py-16">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">LearnLess AI</h1>
        <p className="mt-1 text-muted-foreground">Sign in to your account</p>
      </header>

      {status === "loading" && <p className="text-sm text-muted-foreground">Loading…</p>}

            {status === "authenticated" && <RedirectToDashboard />}
      {status === "unauthenticated" && (
        <Card>
          <CardContent className="pt-5">
            <LoginForm />
          </CardContent>
        </Card>
      )}

      <div className="flex flex-col gap-2 text-sm text-muted-foreground">
        {status === "unauthenticated" && (
          <p>
            Don&apos;t have an account?{" "}
            <Link href="/register" className="font-medium text-primary hover:underline">
              Create one
            </Link>
          </p>
        )}
        <Link href="/" className="hover:underline">
          ← Back to home
        </Link>
      </div>
    </main>
  );
}