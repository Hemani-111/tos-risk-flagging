"use client";

import * as React from "react";
import Link from "next/link";
import { ArrowLeft, Download, Search, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Progress } from "@/components/ui/Progress";
import { AnalysisResult, ClauseResult } from "@/lib/api";
import { clearAnalysisResult, readAnalysisResult } from "@/lib/resultStorage";

type LabelFilter = "All" | "Risky" | "Neutral" | "Safe";
const FILTERS: LabelFilter[] = ["All", "Risky", "Neutral", "Safe"];
const LABEL_STYLES: Record<string, string> = {
  Risky: "bg-red-100 text-red-800 border-red-200",
  Neutral: "bg-yellow-100 text-yellow-900 border-yellow-300",
  Safe: "bg-green-100 text-green-900 border-green-300",
};

function downloadFile(filename: string, content: string, type: string) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function csvCell(value: string | number | undefined) {
  const text = String(value ?? "");
  return `"${text.replaceAll('"', '""')}"`;
}

export default function ResultsPage() {
  const [result, setResult] = React.useState<AnalysisResult | null>(null);
  const [filter, setFilter] = React.useState<LabelFilter>("All");
  const [query, setQuery] = React.useState("");
  const [selectedId, setSelectedId] = React.useState<string | null>(null);

  React.useEffect(() => {
    const frame = window.requestAnimationFrame(() => setResult(readAnalysisResult()));
    return () => window.cancelAnimationFrame(frame);
  }, []);

  const visibleClauses = React.useMemo(() => {
    if (!result) return [];
    const normalizedQuery = query.trim().toLocaleLowerCase();
    return result.clauses.filter((clause) =>
      (filter === "All" || clause.label === filter)
      && (!normalizedQuery || `${clause.text} ${clause.section ?? ""}`.toLocaleLowerCase().includes(normalizedQuery)),
    );
  }, [filter, query, result]);
  const selectedClause = visibleClauses.find((clause) => clause.id === selectedId) ?? visibleClauses[0] ?? null;
  const selectedIndex = selectedClause ? result?.clauses.findIndex((clause) => clause.id === selectedClause.id) ?? -1 : -1;
  const nearbyClauses = selectedIndex < 0 || !result
    ? []
    : result.clauses.slice(Math.max(0, selectedIndex - 1), Math.min(result.clauses.length, selectedIndex + 2));

  if (!result) {
    return (
      <div className="py-16 sm:py-24">
        <div className="mx-auto max-w-3xl px-4 text-center">
          <h1 className="text-3xl font-semibold">No results in this tab</h1>
          <p className="mt-4 text-muted-foreground">Results are kept in this browser tab and clear when the tab session ends.</p>
          <Link href="/analyze"><Button className="mt-6"><ArrowLeft className="mr-2 h-4 w-4" />Analyze a document</Button></Link>
        </div>
      </div>
    );
  }

  const summary = [
    { label: "Risky", count: result.riskyCount, pct: result.riskyPercentage },
    { label: "Neutral", count: result.neutralCount, pct: result.neutralPercentage },
    { label: "Safe", count: result.safeCount, pct: result.safePercentage },
  ];
  const clear = () => {
    clearAnalysisResult();
    setResult(null);
  };
  const exportJson = () => downloadFile("tos-risk-analysis.json", JSON.stringify(result, null, 2), "application/json");
  const exportCsv = () => {
    const columns = ["filename", "modelVersion", "clauseId", "label", "section", "startOffset", "endOffset", "pageStart", "pageEnd", "text"];
    const rows = result.clauses.map((clause) => [
      result.filename, result.modelVersion, clause.id, clause.label, clause.section,
      clause.startOffset, clause.endOffset, clause.pageStart, clause.pageEnd, clause.text,
    ].map(csvCell).join(","));
    downloadFile("tos-risk-clauses.csv", [columns.join(","), ...rows].join("\r\n"), "text/csv;charset=utf-8");
  };

  return (
    <div className="py-8 sm:py-12">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mb-7 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold">Clause review</h1>
            <p className="mt-2 break-all text-sm text-muted-foreground">{result.filename} · {result.totalClauses} clauses · Model {result.modelVersion}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={exportCsv}><Download className="mr-2 h-4 w-4" />Export CSV</Button>
            <Button variant="outline" onClick={exportJson}><Download className="mr-2 h-4 w-4" />Export JSON</Button>
            <Button variant="ghost" onClick={clear}><Trash2 className="mr-2 h-4 w-4" />Clear results</Button>
            <Link href="/analyze"><Button variant="outline"><ArrowLeft className="mr-2 h-4 w-4" />New document</Button></Link>
          </div>
        </div>

        <section aria-label="Clause label summary" className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
          {summary.map((item) => (
            <div key={item.label} className="rounded-lg border border-border bg-card p-5">
              <div className="flex items-center justify-between">
                <span className="font-medium">{item.label}</span>
                <span className="text-2xl font-semibold">{item.count}</span>
              </div>
              <Progress value={item.pct} className="mt-3" />
              <p className="mt-2 text-xs text-muted-foreground">{item.pct.toFixed(1)}% of analyzed clauses</p>
            </div>
          ))}
        </section>

        <section className="mb-6 rounded-lg border border-border bg-secondary/30 p-4" aria-label="Method and limitations">
          <p className="text-sm font-medium">Automated screening, not legal advice</p>
          <p className="mt-1 text-sm text-muted-foreground">These are clause classifications from model {result.modelVersion}; they are not a legal compliance score. The model was trained on annotated excerpts and can miss context or make mistakes.</p>
          {result.warnings?.map((warning) => <p key={warning} className="mt-2 text-xs text-muted-foreground">{warning}</p>)}
          <p className="mt-2 text-xs text-muted-foreground">Results stay in this tab’s session storage. Clear them here or close the tab to remove them.</p>
        </section>

        <section className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
          <div className="border-b border-border p-4 sm:p-5">
            <h2 className="text-xl font-semibold">Review clauses</h2>
            <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="relative w-full sm:max-w-sm">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  aria-label="Search clauses"
                  className="w-full rounded-md border border-input bg-background py-2 pl-9 pr-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  placeholder="Search clause text or section"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                />
              </div>
              <div className="flex flex-wrap gap-2" aria-label="Filter clauses by label">
                {FILTERS.map((label) => (
                  <Button key={label} size="sm" variant={filter === label ? "default" : "outline"} aria-pressed={filter === label} onClick={() => setFilter(label)}>
                    {label}{label === "All" ? ` (${result.clauses.length})` : ` (${result.clauses.filter((clause) => clause.label === label).length})`}
                  </Button>
                ))}
              </div>
            </div>
            <p className="mt-3 text-xs text-muted-foreground" aria-live="polite">Showing {visibleClauses.length} of {result.totalClauses} clauses</p>
          </div>
          <div className="grid gap-0 lg:grid-cols-[minmax(0,1.3fr)_minmax(18rem,0.7fr)]">
            <div className="max-h-[70vh] divide-y divide-border overflow-y-auto">
              {visibleClauses.map((clause: ClauseResult) => (
                <article key={clause.id} className={`p-4 sm:p-5 ${selectedClause?.id === clause.id ? "bg-secondary/50" : ""}`}>
                  <button className="w-full rounded text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" aria-pressed={selectedClause?.id === clause.id} onClick={() => setSelectedId(clause.id)}>
                    <div className="flex items-start justify-between gap-4">
                      <p className="whitespace-pre-wrap text-sm leading-relaxed">{clause.text}</p>
                      <Badge className={`shrink-0 ${LABEL_STYLES[clause.label]}`}>{clause.label}</Badge>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-x-4 text-xs text-muted-foreground">
                      {clause.section && <span>Section: {clause.section}</span>}
                    {clause.pageStart && <span>PDF page{clause.pageEnd !== clause.pageStart ? "s" : ""}: {clause.pageStart}{clause.pageEnd !== clause.pageStart ? `–${clause.pageEnd}` : ""}</span>}
                      <span>Text offsets: {clause.startOffset}–{clause.endOffset}</span>
                    </div>
                  </button>
                </article>
              ))}
              {visibleClauses.length === 0 && <p className="p-8 text-center text-sm text-muted-foreground">No clauses match this search and filter.</p>}
            </div>
            <aside className="border-t border-border bg-secondary/20 p-4 sm:p-5 lg:border-l lg:border-t-0" aria-label="Selected clause context">
              {selectedClause ? <>
                <h3 className="font-semibold">Selected clause</h3>
                <p className="mt-1 text-xs text-muted-foreground">Context uses adjacent analyzable clauses from the extracted text.</p>
                <div className="mt-4 space-y-3" aria-live="polite">
                  {nearbyClauses.map((clause) => (
                    <div key={clause.id} className={`rounded-md border border-border p-3 ${clause.id === selectedClause.id ? "bg-background ring-2 ring-ring" : "bg-card/60"}`}>
                      <div className="mb-2 flex items-center justify-between gap-2">
                        <Badge className={LABEL_STYLES[clause.label]}>{clause.label}</Badge>
                        {clause.id === selectedClause.id && <span className="text-xs font-medium">Selected</span>}
                      </div>
                      <p className="whitespace-pre-wrap text-sm leading-relaxed">{clause.text}</p>
                      {clause.section && <p className="mt-2 text-xs text-muted-foreground">{clause.section}</p>}
                      {clause.pageStart && <p className="mt-1 text-xs text-muted-foreground">PDF page {clause.pageStart}{clause.pageEnd !== clause.pageStart ? `–${clause.pageEnd}` : ""}</p>}
                    </div>
                  ))}
                </div>
              </> : <p className="text-sm text-muted-foreground">Choose a clause to inspect its nearby context.</p>}
            </aside>
          </div>
        </section>
      </div>
    </div>
  );
}
