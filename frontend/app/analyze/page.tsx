"use client";

import * as React from "react";
import { Button } from "@/components/ui/Button";
import { UploadDropzone } from "@/components/upload/UploadDropzone";
import { FilePreview } from "@/components/upload/FilePreview";

export default function AnalyzePage() {
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  
  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setError(null);
  };
  
  const handlePaste = () => {
    const text = prompt("Paste your Terms of Service or Privacy Policy text here:");
    if (text && text.trim().length >= 50) {
      setError("Analysis is not available yet. The model will be connected after training.");
    } else if (text) {
      setError("Text is too short. Please provide at least 50 characters.");
    }
  };
  
  const handleRemove = () => {
    setSelectedFile(null);
    setError(null);
  };
  
  return (
    <div className="py-16 sm:py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center mb-12">
          <h1 className="text-3xl font-semibold">Upload a document</h1>
          <p className="mt-4 text-muted-foreground">
            Select a Terms of Service or Privacy Policy file.
            Document analysis will be available once the ML model is connected.
          </p>
        </div>
        
        {selectedFile ? (
          <FilePreview
            file={selectedFile}
            onRemove={handleRemove}
            onAnalyze={() => {}}
            loading={false}
            disabled={true}
          />
        ) : (
          <UploadDropzone
            onFileSelect={handleFileSelect}
            onPaste={handlePaste}
            onDemo={() => {}}
            loading={false}
          />
        )}
        
        {error && (
          <div className="mt-6 mx-auto max-w-2xl">
            <div className="rounded-md border border-destructive bg-destructive/10 p-4">
              <p className="text-sm text-destructive">{error}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
