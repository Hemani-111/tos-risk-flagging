"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import {
  FiUpload,
  FiFileText,
  FiArrowRight,
  FiClipboard,
} from "react-icons/fi";

const steps = [
  { number: "01", section: "ADD", title: "Start with your policy", detail: "Choose a document or paste its text." },
  { number: "02", section: "FIND", title: "See clause predictions", detail: "Browse Safe, Neutral, and Risky labels." },
  { number: "03", section: "REVIEW", title: "Keep the context", detail: "Jump from each finding to its source." },
];

export default function AnalyzePage() {
  const [activeTab, setActiveTab] = React.useState<"upload" | "paste">("upload");
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const router = useRouter();

  const handleFileSelect = (file: File) => {
    const extension = file.name.split(".").pop()?.toLowerCase();
    if (!["pdf", "docx", "txt"].includes(extension ?? "")) {
      alert("Choose a PDF, DOCX, or TXT file.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      alert("File is larger than the 10 MB upload limit.");
      return;
    }
    setSelectedFile(file);
  };

  const handleRemove = () => {
    setSelectedFile(null);
  };

  const handleAnalyze = () => {
    // Preview only: no backend analysis runs. Open the illustrative sample results.
    router.push("/results");
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="py-12 sm:py-16">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="grid gap-8 lg:grid-cols-2 lg:items-start">
          <div className="space-y-6">
            <span className="inline-flex items-center rounded-full border border-border bg-secondary px-3 py-1 text-xs font-medium text-muted-foreground">
              A little clarity, before you agree
            </span>
            <h1 className="text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
              A closer look at the fine print.
            </h1>
            <p className="text-base leading-7 text-muted-foreground">
              Find flagged clauses, explore their wording, and keep the full document in view.
            </p>
            <Link href="/results">
              <Button size="lg" className="w-full sm:w-auto">
                Explore sample results <FiArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <p className="text-xs text-muted-foreground">
              Educational screening. Your judgment stays central.
            </p>
          </div>

          <div className="rounded-xl border border-border bg-card p-6 sm:p-8 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-foreground">Add a document</h2>
              <span className="text-xs font-medium text-muted-foreground">English-language model</span>
            </div>

            <div className="flex gap-2 border border-border rounded-lg bg-secondary mb-6">
              <button
                onClick={() => setActiveTab("upload")}
                className={`flex-1 py-2.5 text-sm font-medium transition-colors ${
                  activeTab === "upload"
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <FiUpload className="mr-2 h-4 w-4" /> Upload file
              </button>
              <button
                onClick={() => setActiveTab("paste")}
                className={`flex-1 py-2.5 text-sm font-medium transition-colors ${
                  activeTab === "paste"
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <FiClipboard className="mr-2 h-4 w-4" /> Paste text
              </button>
            </div>

            <div
              className={`
                relative rounded-xl border-2 border-dashed p-12 text-center transition-colors min-h-[260px]
                ${"border-border hover:border-primary/50"}
              `}
              onDragEnter={(e) => { e.preventDefault(); }}
              onDragOver={(e) => { e.preventDefault(); }}
              onDragLeave={(e) => { e.preventDefault(); }}
              onDrop={(e) => { e.preventDefault(); if (e.dataTransfer.files[0]) handleFileSelect(e.dataTransfer.files[0]); }}
            >
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={(e) => { if (e.target.files?.[0]) handleFileSelect(e.target.files[0]); }}
                className="hidden"
              />
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-secondary mx-auto mb-3">
                <FiUpload className="h-6 w-6 text-muted-foreground" />
              </div>
              <h3 className="text-sm font-semibold text-foreground mb-1">Drop your policy here</h3>
              <p className="text-xs text-muted-foreground mb-3">PDF, DOCX, TXT · Up to 10 MB</p>
              <button
                onClick={() => {
                  const input = document.querySelector('input[type="file"]') as HTMLInputElement | null;
                  input?.click();
                }}
                className="rounded-md border border-input bg-background px-4 py-2 text-sm font-medium text-foreground hover:bg-accent transition-colors"
              >
                Choose a file
              </button>
              {selectedFile && (
                <div className="mt-4 flex items-center justify-center gap-2 text-xs text-muted-foreground">
                  <FiFileText className="h-4 w-4" />
                  <span>{selectedFile.name} · {formatSize(selectedFile.size)}</span>
                  <button
                    onClick={handleRemove}
                    className="rounded hover:text-foreground underline underline-offset-2"
                  >
                    Remove
                  </button>
                </div>
              )}
            </div>

            <p className="mt-4 text-xs text-muted-foreground leading-relaxed">
              UI preview only. Files stay in this page and are not analyzed.
            </p>

            <div className="mt-6">
              <Button className="w-full" onClick={handleAnalyze}>
                Analyze document <FiArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        <section className="mt-12 border-t border-border pt-8 sm:pt-10">
          <ol className="grid gap-3 sm:grid-cols-3">
            {steps.map((step) => (
              <li key={step.number} className="rounded-lg border border-border p-5 sm:p-6">
                <div className="flex items-start gap-3">
                  <span className="flex shrink-0 h-8 w-8 items-center justify-center rounded-lg bg-secondary text-xs font-semibold text-muted-foreground">
                    {step.number}
                  </span>
                  <div>
                    <p className="text-xs uppercase tracking-wider text-muted-foreground">{step.section}</p>
                    <h3 className="mt-1 text-base font-semibold text-foreground">{step.title}</h3>
                    <p className="mt-1 text-sm leading-6 text-muted-foreground">{step.detail}</p>
                  </div>
                </div>
              </li>
            ))}
          </ol>
        </section>
      </div>
    </div>
  );
}
