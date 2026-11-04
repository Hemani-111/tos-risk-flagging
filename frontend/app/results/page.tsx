"use client";

import * as React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import {
  FiArrowLeft,
  FiDownload,
  FiSearch,
  FiEdit,
  FiType,
} from "react-icons/fi";

type Label = "Safe" | "Neutral" | "Risky";

interface Clause {
  id: string;
  text: string;
  label: Label;
  section?: string;
  startOffset: number;
  endOffset: number;
  pageStart?: number;
  pageEnd?: number;
}

interface SampleResult {
  filename: string;
  totalClauses: number;
  safeCount: number;
  neutralCount: number;
  riskyCount: number;
  safePercentage: number;
  neutralPercentage: number;
  riskyPercentage: number;
  modelVersion: string;
  extractedText: string;
  clauses: Clause[];
}

const LABEL_STYLES: Record<Label, { bg: string; text: string; border: string }> = {
  Risky: { bg: "#fae9e6", text: "#7a2e28", border: "#f5c9c3" },
  Neutral: { bg: "#faf2dd", text: "#7a5d1c", border: "#f0e0ae" },
  Safe: { bg: "#e5f2e9", text: "#3d6a4e", border: "#c9dfcd" },
};

const LABEL_BADGE: Record<Label, string> = {
  Risky: "bg-[#fae9e6] text-[#7a2e28] border-[#f5c9c3]",
  Neutral: "bg-[#faf2dd] text-[#7a5d1c] border-[#f0e0ae]",
  Safe: "bg-[#e5f2e9] text-[#3d6a4e] border-[#c9dfcd]",
};

const FILTER_LABELS: ("All" | Label)[] = ["All", "Risky", "Neutral", "Safe"];

// Illustrative sample data. This preview does not run an ML model.
const SAMPLE: SampleResult = {
  filename: "example-policy.txt",
  totalClauses: 10,
  safeCount: 2,
  neutralCount: 5,
  riskyCount: 3,
  safePercentage: 20,
  neutralPercentage: 50,
  riskyPercentage: 30,
  modelVersion: "illustrative-v1",
  extractedText:
    "EXAMPLE SERVICE\nPOLICY / 01\n\nPrivacy policy\n\nRead each highlighted passage in its full context.\n\n1. About this policy\nThis policy describes how Example Service handles information when you use our website.\n\n2. Information we collect\nWe collect the account details you provide, including your name and email address.\nWe collect device and usage information to operate the service and understand how it is used.\n\n3. Sharing information\nWe may share your information with service providers who help us operate the service.\n\n4. Your choices\nYou can request deletion of your account and associated personal information.\n\n5. Cookies\nWe use cookies to personalize your experience and analyze traffic.\n\n6. Security\nYour data is encrypted in transit and at rest.\n\n7. Location\nWe collect location data from your device when you use the app.\n\n8. Marketing\nYou may opt out of marketing emails at any time.\n\n9. Changes to this policy\nWe may change these terms at any time without notifying you individually.\n",
  clauses: [
    {
      id: "clause-01",
      text: "This policy describes how Example Service handles information when you use our website.",
      label: "Neutral",
      section: "1. About this policy",
      startOffset: 91,
      endOffset: 192,
    },
    {
      id: "clause-02",
      text: "We collect the account details you provide, including your name and email address.",
      label: "Neutral",
      section: "2. Information we collect",
      startOffset: 214,
      endOffset: 314,
    },
    {
      id: "clause-03",
      text: "We collect device and usage information to operate the service and understand how it is used.",
      label: "Neutral",
      section: "2. Information we collect",
      startOffset: 316,
      endOffset: 463,
    },
    {
      id: "clause-04",
      text: "We may share your information with service providers who help us operate the service.",
      label: "Risky",
      section: "3. Sharing information",
      startOffset: 485,
      endOffset: 596,
    },
    {
      id: "clause-05",
      text: "You can request deletion of your account and associated personal information.",
      label: "Safe",
      section: "4. Your choices",
      startOffset: 618,
      endOffset: 717,
    },
    {
      id: "clause-06",
      text: "We use cookies to personalize your experience and analyze traffic.",
      label: "Neutral",
      section: "5. Cookies",
      startOffset: 739,
      endOffset: 826,
    },
    {
      id: "clause-07",
      text: "Your data is encrypted in transit and at rest.",
      label: "Safe",
      section: "6. Security",
      startOffset: 848,
      endOffset: 906,
    },
    {
      id: "clause-08",
      text: "We collect location data from your device when you use the app.",
      label: "Risky",
      section: "7. Location",
      startOffset: 928,
      endOffset: 1011,
    },
    {
      id: "clause-09",
      text: "You may opt out of marketing emails at any time.",
      label: "Safe",
      section: "8. Marketing",
      startOffset: 1033,
      endOffset: 1110,
    },
    {
      id: "clause-10",
      text: "We may change these terms at any time without notifying you individually.",
      label: "Risky",
      section: "9. Changes to this policy",
      startOffset: 1132,
      endOffset: 1225,
    },
  ],
};

function offsetText(text: string, start: number, end: number) {
  return text.slice(start, end);
}

export default function ResultsPage() {
  const result = SAMPLE;
  const [filter, setFilter] = React.useState<Label | "All">("All");
  const [query, setQuery] = React.useState("");
  const [selectedId, setSelectedId] = React.useState<string | null>(result.clauses[0]?.id ?? null);

  const visibleClauses = React.useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return result.clauses.filter((clause) =>
      (filter === "All" || clause.label === filter) &&
      (!normalizedQuery ||
        `${clause.text} ${clause.section ?? ""}`.toLowerCase().includes(normalizedQuery))
    );
  }, [filter, query, result]);

  const selectedClause =
    visibleClauses.find((clause) => clause.id === selectedId) ?? visibleClauses[0] ?? null;
  const selectedIndex = selectedClause ? result.clauses.findIndex((c) => c.id === selectedClause.id) : -1;
  const nearbyClauses =
    selectedIndex < 0
      ? []
      : result.clauses.slice(Math.max(0, selectedIndex - 1), Math.min(result.clauses.length, selectedIndex + 2));

  // Build plain/highlighted segments for the document reader.
  const sourceSegments = React.useMemo(() => {
    const ordered = [...result.clauses]
      .filter(
        (c) =>
          Number.isInteger(c.startOffset) &&
          Number.isInteger(c.endOffset) &&
          c.startOffset >= 0 &&
          c.endOffset > c.startOffset &&
          c.endOffset <= result.extractedText.length
      )
      .sort((a, b) => a.startOffset - b.startOffset || a.endOffset - b.endOffset);
    const segments: Array<{ start: number; end: number; clause: Clause | null }> = [];
    let cursor = 0;
    for (const clause of ordered) {
      if (clause.startOffset < cursor) continue;
      if (clause.startOffset > cursor)
        segments.push({ start: cursor, end: clause.startOffset, clause: null });
      segments.push({ start: clause.startOffset, end: clause.endOffset, clause });
      cursor = clause.endOffset;
    }
    if (cursor < result.extractedText.length)
      segments.push({ start: cursor, end: result.extractedText.length, clause: null });
    return segments;
  }, [result]);

  const selectSourceClause = (clause: Clause) => {
    setFilter("All");
    setQuery("");
    setSelectedId(clause.id);
    const el = document.querySelector(`[data-source-clause="${CSS.escape(clause.id)}"]`);
    el?.scrollIntoView({ block: "center", behavior: "smooth" });
  };

  const summary = [
    { label: "Risky" as const, count: result.riskyCount, pct: result.riskyPercentage },
    { label: "Neutral" as const, count: result.neutralCount, pct: result.neutralPercentage },
    { label: "Safe" as const, count: result.safeCount, pct: result.safePercentage },
  ];

  const downloadFile = (filename: string, content: string, type: string) => {
    const url = URL.createObjectURL(new Blob([content], { type }));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const csvCell = (value: string | number | undefined) => {
    const text = String(value ?? "");
    return `"${text.replaceAll('"', '""')}"`;
  };

  const exportCsv = () => {
    const columns = ["filename", "clauseId", "label", "section", "startOffset", "endOffset", "text"];
    const rows = result.clauses.map((clause) =>
      [result.filename, clause.id, clause.label, clause.section, clause.startOffset, clause.endOffset, clause.text]
        .map(csvCell)
        .join(",")
    );
    downloadFile("tos-risk-clauses.csv", [columns.join(","), ...rows].join("\r\n"), "text/csv;charset=utf-8");
  };

  return (
    <div className="results-page py-8 sm:py-12">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        {/* Workspace header */}
        <div className="mb-2 flex items-center gap-1 text-xs font-medium text-muted-foreground">
          <span>Workspace</span>
          <span aria-hidden="true">/</span>
          <span>Document review</span>
        </div>
        <div className="mb-8 flex flex-wrap items-center justify-between gap-3 sm:justify-end">
          <div>
            <h1 className="text-3xl font-semibold text-foreground">Privacy policy</h1>
            <p className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">
              <span className="flex h-6 w-6 items-center justify-center rounded-full border border-border bg-background px-1.5">
                <span className="h-[8px] w-[8px] rounded-full bg-primary" aria-hidden="true" />
              </span>
              <span>{result.filename}</span>
              <span className="inline-flex items-center rounded-md border border-border bg-secondary px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                Illustrative sample
              </span>
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={exportCsv}>
              <FiDownload className="mr-2 h-4 w-4" /> Export
            </Button>
            <Link href="/">
              <Button className="whitespace-nowrap"><FiArrowLeft className="mr-2 h-4 w-4" /> New analysis</Button>
            </Link>
          </div>
        </div>

        {/* Summary row */}
        <section aria-label="Clause label summary" className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
          {summary.map((item) => (
            <div key={item.label} className="rounded-xl border border-border bg-card p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-wider text-muted-foreground">{item.label} clauses</p>
                  <span className="text-2xl font-semibold text-foreground">{item.count}</span>
                </div>
                <Badge className={LABEL_BADGE[item.label]}>{item.label}</Badge>
              </div>
              <div className="mt-3 h-1.5 w-full rounded-full bg-secondary overflow-hidden">
                <div
                  className="h-full"
                  style={{ width: `${item.pct}%`, backgroundColor: LABEL_STYLES[item.label].bg }}
                />
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                {item.pct.toFixed(0)}% of clauses
              </p>
            </div>
          ))}
        </section>

        <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
          {/* Document reader */}
          <section className="col-span-1 lg:col-span-1 mb-6 lg:mb-0 overflow-hidden rounded-xl border border-border bg-card shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border p-4 sm:p-5">
              <div>
                <h2 className="text-sm font-semibold text-foreground">Extracted document</h2>
                <p className="mt-1 text-xs text-muted-foreground">Clause spans are highlighted in place.</p>
              </div>
              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                <button className="flex items-center gap-1.5 hover:text-foreground transition-colors">
                  <FiEdit className="h-3.5 w-3.5" /> Highlights on
                </button>
                <span className="h-[1px] w-px bg-border" aria-hidden="true" />
                <button className="flex items-center gap-1.5 hover:text-foreground transition-colors">
                  <FiType className="h-3.5 w-3.5" /> 16 px
                </button>
              </div>
            </div>
            <div className="relative max-h-[70vh] overflow-auto bg-background p-4 sm:p-6 font-sans text-sm leading-7">
              <div className="relative">
                {/* clause number margin */}
                <div className="absolute left-0 top-0 bottom-0 w-4 text-[11px] text-muted-foreground pointer-events-none select-none">
                  {result.clauses.map((c) => (
                    <div key={c.id} className="mt-[14px] text-center font-medium text-muted-foreground/60">
                      {c.id.replace("clause-", "")}
                    </div>
                  ))}
                </div>
                <div className="pl-10 whitespace-pre-wrap break-words" aria-label={`Extracted text from ${result.filename}`}>
                  {sourceSegments.map((segment, index) => segment.clause ? (
                    <mark
                      key={`${segment.start}-${segment.end}-${segment.clause.id}`}
                      data-source-clause={segment.clause.id}
                      title={`${segment.clause.label}${segment.clause.section ? " · " + segment.clause.section : ""}`}
                      role="button"
                      tabIndex={0}
                      aria-label={`Select ${segment.clause.label} clause ${segment.clause.id}`}
                      onClick={() => selectSourceClause(segment.clause!)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          selectSourceClause(segment.clause!);
                        }
                      }}
                      className={`cursor-pointer rounded-sm px-0.5 text-inherit transition-colors ${
                        selectedClause?.id === segment.clause.id
                          ? "ring-2 ring-ring ring-offset-1"
                          : ""
                      }`}
                      style={{
                        backgroundColor: LABEL_STYLES[segment.clause.label].bg,
                        color: LABEL_STYLES[segment.clause.label].text,
                        border: `1px solid ${LABEL_STYLES[segment.clause.label].border}`,
                      }}
                    >
                      {offsetText(result.extractedText, segment.start, segment.end)}
                    </mark>
                  ) : (
                    <span key={`plain-${segment.start}-${index}`}>
                      {offsetText(result.extractedText, segment.start, segment.end)}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* Clause inspector */}
          <section className="col-span-1 lg:col-span-1 overflow-hidden rounded-xl border border-border bg-card shadow-sm">
            <div className="border-b border-border p-4 sm:p-5">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-semibold text-foreground">Review clauses</h2>
                <span className="text-xs text-muted-foreground">{visibleClauses.length} / {result.totalClauses}</span>
              </div>
              <div className="relative mb-4">
                <FiSearch className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground pointer-events-none" />
                <input
                  aria-label="Search clauses"
                  className="w-full rounded-md border border-input bg-background pl-9 pr-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  placeholder="Search clauses..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
              </div>
              <div className="flex flex-wrap gap-2" aria-label="Filter clauses by label">
                {FILTER_LABELS.map((label) => {
                  const count =
                    label === "All"
                      ? result.totalClauses
                      : result.clauses.filter((c) => c.label === label).length;
                  const visibleCount =
                    label === "All"
                      ? visibleClauses.length
                      : visibleClauses.filter((c) => c.label === label).length;
                  return (
                    <Button
                      key={label}
                      size="sm"
                      variant={filter === label ? "default" : "outline"}
                      aria-pressed={filter === label}
                      onClick={() => setFilter(label)}
                      className="text-[12px] px-2 py-1.5"
                    >
                      {label} {filter === label ? `(${visibleCount})` : `(${count})`}
                    </Button>
                  );
                })}
              </div>
              <p className="mt-3 text-xs text-muted-foreground" aria-live="polite">
                Showing {visibleClauses.length} of {result.totalClauses} clauses
              </p>
            </div>
            <div className="max-h-[65vh] overflow-y-auto divide-y divide-border p-2 sm:p-3">
              {visibleClauses.map((clause) => (
                <button
                  key={clause.id}
                  onClick={() => setSelectedId(clause.id)}
                  aria-pressed={selectedId === clause.id}
                  className={`w-full rounded-lg p-3 sm:p-4 text-left transition-colors ${
                    selectedId === clause.id
                      ? "bg-[#f8faf7] ring-1 ring-ring"
                      : "hover:bg-secondary/50"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">{clause.text}</p>
                    <Badge className={`shrink-0 ${LABEL_BADGE[clause.label]}`}>{clause.label}</Badge>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-x-3 text-[11px] text-muted-foreground">
                    {clause.section && <span>{clause.section}</span>}
                    {clause.pageStart && (
                      <span>
                        PDF page {clause.pageStart}{clause.pageEnd !== clause.pageStart ? `–${clause.pageEnd}` : ""}
                      </span>
                    )}
                  </div>
                </button>
              ))}
              {visibleClauses.length === 0 && (
                <p className="p-8 text-center text-sm text-muted-foreground">
                  No clauses match this search and filter.
                </p>
              )}
            </div>
            <div className="border-t border-border bg-secondary/20 p-4 sm:p-5" aria-label="Selected clause context">
              {selectedClause ? (
                <>
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
                    Selected clause
                  </h3>
                  <div className="space-y-3">
                    {nearbyClauses.map((clause) => (
                      <div
                        key={clause.id}
                        className={`rounded-md border p-3 ${
                          clause.id === selectedClause.id
                            ? "bg-background ring-1 ring-ring"
                            : "bg-secondary/40"
                        }`}
                      >
                        <div className="mb-2 flex items-center justify-between gap-2">
                          <Badge className={LABEL_BADGE[clause.label]}>{clause.label}</Badge>
                          {clause.id === selectedClause.id && (
                            <span className="text-[10px] font-medium text-foreground">Selected</span>
                          )}
                        </div>
                        <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">
                          {clause.text}
                        </p>
                        {clause.section && (
                          <p className="mt-1 text-[11px] text-muted-foreground">{clause.section}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">Choose a clause to inspect its nearby context.</p>
              )}
            </div>
          </section>
        </div>

        <p className="mt-8 flex items-center gap-2 text-xs text-muted-foreground">
          <span className="h-3.5 w-3.5 rounded-full" style={{ backgroundColor: "#dce5de" }} aria-hidden="true" />
          Educational screening, not legal advice. Labels may be incorrect.
        </p>
      </div>
    </div>
  );
}
