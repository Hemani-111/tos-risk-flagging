"use client";

import * as React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Progress } from "@/components/ui/Progress";
import { ArrowLeft, AlertTriangle, ShieldCheck, MinusCircle } from "lucide-react";
import { AnalysisResult, ClauseResult } from "@/lib/api";

function parseResult(encoded: string): AnalysisResult {
  return JSON.parse(decodeURIComponent(escape(atob(encoded))));
}

const LABEL_STYLES: Record<string, string> = {
  Risky: "bg-red-100 text-red-800 border-red-200",
  Neutral: "bg-yellow-100 text-yellow-800 border-yellow-200",
  Safe: "bg-green-100 text-green-800 border-green-200",
};

export default function ResultsPage({
  searchParams,
}: {
  searchParams: { data?: string };
}) {
  const result: AnalysisResult | null = React.useMemo(() => {
    if (!searchParams?.data) return null;
    try {
      return parseResult(searchParams.data);
    } catch {
      return null;
    }
  }, [searchParams?.data]);

  if (!result) {
    return (
      <div className="py-16 sm:py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h1 className="text-3xl font-semibold">No analysis data</h1>
            <p className="mt-4 text-muted-foreground">
              Upload a document first to see results.
            </p>
            <Link href="/analyze">
              <Button className="mt-6">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Go to upload
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const summary = [
    { label: "Safe", count: result.safeCount, pct: result.safePercentage, icon: ShieldCheck, color: "text-green-600" },
    { label: "Neutral", count: result.neutralCount, pct: result.neutralPercentage, icon: MinusCircle, color: "text-yellow-600" },
    { label: "Risky", count: result.riskyCount, pct: result.riskyPercentage, icon: AlertTriangle, color: "text-red-600" },
  ];
  // Results opened from a previously generated URL may predate riskyClauses.
  // Derive the display list from the original per-clause predictions then.
  const riskyClauses = result.riskyClauses ?? result.clauses.filter((clause) => clause.label === "Risky");

  return (
    <div className="py-16 sm:py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-semibold">Analysis results</h1>
            <p className="mt-2 text-muted-foreground">
              {result.filename} • {result.totalClauses} clauses analyzed
            </p>
          </div>
          <Link href="/analyze">
            <Button variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" />
              New document
            </Button>
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {summary.map((item) => (
            <div key={item.label} className="rounded-lg border border-border bg-card p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-muted-foreground">{item.label}</span>
                <item.icon className={`h-5 w-5 ${item.color}`} />
              </div>
              <div className="text-3xl font-semibold">{item.count}</div>
              <Progress value={item.pct} className="mt-3" />
              <p className="mt-2 text-xs text-muted-foreground">{item.pct.toFixed(1)}% of clauses</p>
            </div>
          ))}
        </div>

        <div className="rounded-lg border border-border bg-card p-6 mb-8">
          <h2 className="text-lg font-semibold mb-2">Overall assessment</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">{result.overallAssessment}</p>
          <p className="mt-3 text-xs text-muted-foreground">
            Model {result.modelVersion} · Results are clause classifications, not a legal compliance assessment.
          </p>
          {result.warnings?.length > 0 && (
            <ul className="mt-3 list-disc space-y-1 pl-5 text-xs text-muted-foreground">
              {result.warnings.map((warning) => <li key={warning}>{warning}</li>)}
            </ul>
          )}
        </div>

        <div className="rounded-lg border border-border bg-card">
          <div className="p-6 border-b border-border">
            <h2 className="text-lg font-semibold">{result.riskyCount} Risky statements detected</h2>
          </div>
          <div className="divide-y divide-border">
            {riskyClauses.map((clause: ClauseResult) => (
              <div key={clause.id} className="p-4 sm:p-6">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <p className="text-sm leading-relaxed">{clause.text}</p>
                    {clause.section && (
                      <p className="mt-2 text-xs text-muted-foreground">{clause.section}</p>
                    )}
                  </div>
                  <Badge className={`shrink-0 ${LABEL_STYLES[clause.label] || ""}`}>
                    {clause.label}
                  </Badge>
                </div>
              </div>
            ))}
            {riskyClauses.length === 0 && (
              <p className="p-6 text-sm text-muted-foreground">No risky statements were detected.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
