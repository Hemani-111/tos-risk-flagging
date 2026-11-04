const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API}${path}`, options);
  } catch {
    throw new Error('The analysis server could not be reached. Check that it is running, then retry.');
  }
  if (!response.ok) {
    let message = `Analysis failed (${response.status}).`;
    try {
      const data = await response.json();
      if (typeof data.detail === 'string') message = data.detail;
      else if (data.detail) message = JSON.stringify(data.detail);
    } catch {
      const text = await response.text().catch(() => '');
      if (text) message = text;
    }
    throw new Error(message);
  }
  return response.json();
}

function readField(value, camel, snake) {
  return value?.[camel] ?? value?.[snake];
}

export function normalize(data) {
  if (!Array.isArray(data?.clauses)) throw new Error('The server response does not contain a clauses array.');
  const extractedText = data.extractedText ?? data.extracted_text ?? '';
  const clauses = data.clauses.map((clause, index) => {
    const startOffset = Number(readField(clause, 'startOffset', 'start_offset') ?? 0);
    const endOffset = Number(readField(clause, 'endOffset', 'end_offset') ?? startOffset);
    const label = clause.label ?? clause.prediction ?? 'Neutral';
    return {
      id: String(clause.id ?? index + 1),
      text: clause.text ?? clause.clause_text ?? extractedText.slice(startOffset, endOffset),
      label: ['Risky', 'Neutral', 'Safe'].includes(label) ? label : 'Neutral',
      section: clause.section ?? clause.section_heading ?? '',
      startOffset,
      endOffset,
      pageStart: readField(clause, 'pageStart', 'page_start'),
      pageEnd: readField(clause, 'pageEnd', 'page_end'),
    };
  });
  return {
    id: data.id,
    filename: data.filename || 'pasted-text.txt',
    title: data.filename || 'Document review',
    extractedText,
    clauses,
    totalClauses: data.totalClauses ?? data.total_clauses ?? clauses.length,
    riskyCount: data.riskyCount ?? data.risky_count ?? clauses.filter((clause) => clause.label === 'Risky').length,
    neutralCount: data.neutralCount ?? data.neutral_count ?? clauses.filter((clause) => clause.label === 'Neutral').length,
    safeCount: data.safeCount ?? data.safe_count ?? clauses.filter((clause) => clause.label === 'Safe').length,
    modelVersion: data.modelVersion ?? data.model_version ?? 'Unknown',
    schemaVersion: data.schemaVersion ?? data.schema_version ?? 'Unknown',
    warnings: data.warnings ?? [],
    overallAssessment: data.overallAssessment ?? data.overall_assessment,
    sections: [],
  };
}
