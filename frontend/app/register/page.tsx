"use client";

import Link from "next/link";
import { useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { RedirectToDashboard } from "@/components/redirect-to-dashboard";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api";
import { fieldErrorsFrom } from "@/lib/form-errors";

// The form is its own component, so it is removed while you are signed in and
// comes back with empty fields and no old errors after you sign out.
function RegisterForm() {
  const { register } = useAuth();

  const [fullName, setFullName] = useState("");
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
      await register({
        email: email.trim(),
        password,
        full_name: fullName.trim(),
      });
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

      <FormField id="full_name" label="Full name" error={fieldErrors.full_name}>
        <Input
          id="full_name"
          name="full_name"
          type="text"
          autoComplete="name"
          required
          maxLength={255}
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          disabled={submitting}
        />
      </FormField>

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
          autoComplete="new-password"
          required
          minLength={8}
          maxLength={72}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={submitting}
        />
        <p className="text-xs text-muted-foreground">8 to 72 characters.</p>
      </FormField>

      <Button type="submit" disabled={submitting}>
        {submitting ? "Creating account…" : "Create account"}
      </Button>
    </form>
  );
}

export default function RegisterPage() {
  const { status } = useAuth();

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-6 px-6 py-16">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">LearnLess AI</h1>
        <p className="mt-1 text-muted-foreground">Create your account</p>
      </header>

      {status === "loading" && <p className="text-sm text-muted-foreground">Loading…</p>}

      {status === "authenticated" && <RedirectToDashboard />}

      {status === "unauthenticated" && (
        <Card>
          <CardContent className="pt-5">
            <RegisterForm />
          </CardContent>
        </Card>
      )}

      <div className="flex flex-col gap-2 text-sm text-muted-foreground">
        {status === "unauthenticated" && (
          <p>
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-primary hover:underline">
              Sign in
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