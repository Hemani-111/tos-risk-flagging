export interface DocumentInfo {
  filename: string;
  title?: string;
  file_type?: string;
}

export interface ClauseResult {
  id: string;
  text: string;
  label: "Safe" | "Neutral" | "Risky";
  section?: string;
  startOffset: number;
  endOffset: number;
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
