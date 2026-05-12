"use client";

import { ErrorState } from "@/components/chrome/error-state";

const PROJECT_ROOT_HINT =
  "Set PRAXION_PROJECT_ROOT to your project's absolute path, or relaunch via `praxion-dashboard start <path>`.";

interface ErrorBoundaryProps {
  error: Error;
  reset: () => void;
}

export default function GlobalError({ error, reset }: ErrorBoundaryProps) {
  const isProjectRootError =
    error.message.includes("PRAXION") ||
    error.message.includes("project root") ||
    error.message.includes("required directories");

  return (
    <div className="error-page">
      <ErrorState
        hint={isProjectRootError ? PROJECT_ROOT_HINT : undefined}
        message={error.message}
        retry={reset}
        title="Something went wrong"
      />
    </div>
  );
}
