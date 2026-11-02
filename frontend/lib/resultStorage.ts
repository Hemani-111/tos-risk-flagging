import type { AnalysisResult } from "./api";

const RESULT_KEY = "tos-risk-analysis-result-v1";

export function saveAnalysisResult(result: AnalysisResult): void {
  try {
    // Keep exact source text and offsets; reconstruct clause strings on read to
    // avoid storing every highlighted segment a second time.
    const compact = {
      ...result,
      clauses: result.clauses.map((clause) => ({ ...clause, text: "" })),
      riskyClauses: [],
    };
    sessionStorage.setItem(RESULT_KEY, JSON.stringify(compact));
  } catch {
    throw new Error("Results could not be stored in this browser tab. Try a smaller document.");
  }
}

export function readAnalysisResult(): AnalysisResult | null {
  try {
    const value = sessionStorage.getItem(RESULT_KEY);
    if (!value) return null;
    const result = JSON.parse(value) as AnalysisResult;
    if (typeof result.extractedText === "string") {
      result.clauses = result.clauses.map((clause) => ({
        ...clause,
        text: result.extractedText.slice(clause.startOffset, clause.endOffset),
      }));
      result.riskyClauses = result.clauses.filter((clause) => clause.label === "Risky");
    }
    return result;
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
