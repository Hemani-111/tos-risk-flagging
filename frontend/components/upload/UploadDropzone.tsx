"use client";

import * as React from "react";
import { Upload as UploadIcon, FileText } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface UploadDropzoneProps {
  onFileSelect: (file: File) => void;
  onPaste: () => void;
  onDemo?: () => void;
  loading?: boolean;
}

export function UploadDropzone({ onFileSelect, onPaste, loading }: UploadDropzoneProps) {
  const [dragActive, setDragActive] = React.useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };
  
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  };
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    }
  };
  
  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        className={`
          relative rounded-lg border-2 border-dashed p-12 text-center transition-colors
          ${dragActive
            ? "border-primary bg-primary/5"
            : "border-border hover:border-primary/50"
          }
        `}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={handleChange}
          className="hidden"
          disabled={loading}
        />
        
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-muted mb-4">
          <FileText className="h-8 w-8 text-muted-foreground" />
        </div>
        
        <h3 className="text-lg font-semibold mb-2">
          Drop your Terms of Service here
        </h3>
        <p className="text-sm text-muted-foreground mb-4">
          or choose a file
        </p>
        <p className="text-xs text-muted-foreground mb-6">
          Supports PDF, DOCX, TXT (max 10MB)
        </p>
        
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button
            onClick={() => fileInputRef.current?.click()}
            disabled={loading}
          >
            <UploadIcon className="mr-2 h-4 w-4" />
            Choose file
          </Button>
          <Button variant="outline" onClick={onPaste} disabled={loading}>
            Paste text instead
          </Button>
        </div>
      </div>
    </div>
  );
}
