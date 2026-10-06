import { ServiceStatus } from "@/components/service-status";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-8 px-6 py-16">
      <header>
        <h1 className="text-4xl font-bold tracking-tight">LearnLess AI</h1>
        <p className="mt-2 text-lg text-muted-foreground">Learn More. Watch Less.</p>
      </header>
      <ServiceStatus />
      <p className="text-sm text-muted-foreground">
        Phase 1 foundation. Sign-in, courses and AI features are added in later phases.
      </p>
    </main>
  );
}
