import type { AnalysisResult } from "./api";

const RESULT_KEY = "tos-risk-analysis-result-v1";

export function saveAnalysisResult(result: AnalysisResult): void {
  try {
    sessionStorage.setItem(RESULT_KEY, JSON.stringify(result));
  } catch {
    throw new Error("Results could not be stored in this browser tab. Try a smaller document.");
  }
}

export function readAnalysisResult(): AnalysisResult | null {
  try {
    const value = sessionStorage.getItem(RESULT_KEY);
    if (!value) return null;
    return JSON.parse(value) as AnalysisResult;
  } catch {
    return null;
  }
}

export function clearAnalysisResult(): void {
  try {
    sessionStorage.removeItem(RESULT_KEY);
  } catch {
    // Storage may be disabled; removing the in-memory result still clears the view.
  }
}
