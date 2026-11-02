"use client";

import * as React from "react";
import { Button } from "@/components/ui/Button";
import { UploadDropzone } from "@/components/upload/UploadDropzone";
import { FilePreview } from "@/components/upload/FilePreview";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/Dialog";
import { analyzeDocument, analyzeText } from "@/lib/api";
import { useRouter } from "next/navigation";
import { saveAnalysisResult } from "@/lib/resultStorage";

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Analysis failed.";
}

export default function AnalyzePage() {
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [isPasteModalOpen, setIsPasteModalOpen] = React.useState(false);
  const [pastedText, setPastedText] = React.useState("");
  const router = useRouter();

  const handleFileSelect = (file: File) => {
    const extension = file.name.split(".").pop()?.toLowerCase();
    if (!["pdf", "docx", "txt"].includes(extension ?? "")) {
      setError("Choose a PDF, DOCX, or TXT file.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("File is larger than the 10 MB upload limit.");
      return;
    }
    setSelectedFile(file);
    setError(null);
  };

  const handlePaste = () => {
    setPastedText("");
    setIsPasteModalOpen(true);
  };

  const handlePasteSubmit = async () => {
    if (!pastedText || pastedText.trim().length < 50) {
      setError("Text is too short. Please provide at least 50 characters.");
      return;
    }
    if (pastedText.length > 2_000_000) {
      setError("Pasted text is larger than the 2,000,000 character limit.");
      return;
    }
    setLoading(true);
    setError(null);
    setIsPasteModalOpen(false);
    try {
      const result = await analyzeText(pastedText.trim());
      saveAnalysisResult(result);
      router.push("/results");
    } catch (err: unknown) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handlePasteCancel = () => {
    setIsPasteModalOpen(false);
    setPastedText("");
  };

  const handleRemove = () => {
    setSelectedFile(null);
    setError(null);
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;
    setLoading(true);
    setError(null);
    try {
      const result = await analyzeDocument(selectedFile);
      saveAnalysisResult(result);
      router.push("/results");
    } catch (err: unknown) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="py-12 sm:py-16">
      <div className="mx-auto max-w-5xl px-4 sm:px-6">
        <div className="mx-auto mb-9 max-w-2xl text-center">
          <p className="text-sm font-medium text-muted-foreground">Document review</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">Analyze a policy</h1>
          <p className="mt-3 leading-6 text-muted-foreground">
            Upload a Terms of Service or Privacy Policy to review its extracted clauses.
          </p>
          <p className="mt-3 text-sm text-muted-foreground">PDF, DOCX, or TXT · 10 MB maximum · English-language model</p>
        </div>

        <p className="mx-auto mb-6 max-w-2xl text-center text-xs leading-relaxed text-muted-foreground">
          Files are sent to the configured backend for analysis and removed from its temporary storage afterward. Results stay in this browser tab only. Do not upload documents you are not permitted to share.
        </p>

        {selectedFile ? (
          <FilePreview
            file={selectedFile}
            onRemove={handleRemove}
            onAnalyze={handleAnalyze}
            loading={loading}
            disabled={false}
          />
        ) : (
          <UploadDropzone
            onFileSelect={handleFileSelect}
            onPaste={handlePaste}
            onDemo={() => {}}
            loading={loading}
          />
        )}

        {error && (
          <div className="mt-6 mx-auto max-w-2xl">
            <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4" role="alert">
              <p className="text-sm text-destructive">{error}</p>
            </div>
          </div>
        )}

        <Dialog open={isPasteModalOpen} onOpenChange={(open) => !open && handlePasteCancel()}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Paste your text</DialogTitle>
              <DialogDescription>
                Paste or type your Terms of Service or Privacy Policy below. You can edit the text before analyzing.
              </DialogDescription>
            </DialogHeader>

            <div className="mt-4">
              <textarea
                aria-label="Document text to analyze"
                value={pastedText}
                onChange={(e) => setPastedText(e.target.value.slice(0, 2_000_000))}
                placeholder="Paste your document text here..."
                className="w-full h-64 rounded-md border border-input bg-background p-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-y"
              />
              <p className="mt-2 text-xs text-muted-foreground">
                {pastedText.length.toLocaleString()} / 2,000,000 characters. Minimum 50 characters required.
              </p>
            </div>

            <DialogFooter className="mt-4">
              <Button variant="outline" onClick={handlePasteCancel} disabled={loading}>
                Cancel
              </Button>
              <Button onClick={handlePasteSubmit} disabled={loading || pastedText.trim().length < 50}>
                {loading ? "Analyzing..." : "Analyze"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
