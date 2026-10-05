"use client";

import * as React from "react";
import { FileText, X } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface FilePreviewProps {
  file: File;
  onRemove: () => void;
  onAnalyze?: () => void;
  loading?: boolean;
  disabled?: boolean;
}

export function FilePreview({ file, onRemove, onAnalyze, loading, disabled }: FilePreviewProps) {
  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };
  
  const getFileType = (file: File) => {
    const ext = file.name.split(".").pop()?.toUpperCase();
    return ext || "FILE";
  };
  
  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="rounded-lg border border-border bg-card p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-muted">
              <FileText className="h-6 w-6 text-muted-foreground" />
            </div>
            <div>
              <p className="text-sm font-medium">{file.name}</p>
              <p className="text-xs text-muted-foreground">
                {getFileType(file)} • {formatSize(file.size)}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button variant="ghost" size="icon" onClick={onRemove} disabled={loading}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
        
        {onAnalyze && (
          <div className="mt-4 flex justify-end">
            <Button onClick={onAnalyze} disabled={loading || disabled}>
              {loading ? "Analyzing..." : "Analyze document"}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
