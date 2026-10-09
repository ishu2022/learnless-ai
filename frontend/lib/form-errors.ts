import type { ApiError } from "@/lib/api";
import type { ValidationIssue } from "@/types/auth";

// The backend answers validation problems (HTTP 422) with a list of issues.
// Each issue's "loc" ends with the field name, e.g. ["body", "email"].
export function fieldErrorsFrom(error: ApiError): Record<string, string> {
  if (error.status !== 422 || !Array.isArray(error.details)) return {};
  const result: Record<string, string> = {};
  for (const issue of error.details as ValidationIssue[]) {
    const field = issue.loc[issue.loc.length - 1];
    if (typeof field === "string" && !(field in result)) {
      result[field] = issue.msg;
    }
  }
  return result;
}