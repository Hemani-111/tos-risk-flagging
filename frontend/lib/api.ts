const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function healthCheck(): Promise<{ status: string }> {
  const res = await fetch(`${API_URL}/api/v1/health`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Backend unavailable");
  return res.json();
}

export interface ClauseResult {
  id: string;
  text: string;
  label: "Safe" | "Neutral" | "Risky";
  section?: string;
  startOffset: number;
  endOffset: number;
  pageStart?: number;
  pageEnd?: number;
}

export interface AnalysisResult {
  id: string;
  filename: string;
  totalClauses: number;
  safeCount: number;
  neutralCount: number;
  riskyCount: number;
  safePercentage: number;
  neutralPercentage: number;
  riskyPercentage: number;
  overallAssessment: string;
  modelVersion: string;
  schemaVersion: string;
  warnings: string[];
  clauses: ClauseResult[];
  riskyClauses: ClauseResult[];
}

export async function analyzeDocument(file: File): Promise<AnalysisResult> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_URL}/api/v1/documents/analyze`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const text = await res.text();
    let message = `Analysis failed (${res.status})`;
    try {
      const data = await res.json();
      if (data.detail) message = data.detail;
    } catch {
      if (text) message = text;
    }
    throw new Error(message);
  }

  return res.json();
}

export async function analyzeText(text: string, filename = "pasted-text.txt"): Promise<AnalysisResult> {
  const res = await fetch(`${API_URL}/api/v1/documents/analyze-text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, filename }),
  });

  if (!res.ok) {
    const body = await res.text();
    let message = `Analysis failed (${res.status})`;
    try {
      const data = await res.json();
      if (data.detail) message = data.detail;
    } catch {
      if (body) message = body;
    }
    throw new Error(message);
  }

  return res.json();
}
