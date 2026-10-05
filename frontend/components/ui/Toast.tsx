import * as React from "react";

interface ToastProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  description?: string;
  variant?: "default" | "destructive";
}

export function Toast({ open, onOpenChange, title, description, variant = "default" }: ToastProps) {
  if (!open) return null;
  
  return (
    <div className="fixed bottom-4 right-4 z-50">
      <div
        className={`
          rounded-lg border p-4 shadow-lg
          ${variant === "destructive"
            ? "border-destructive bg-destructive text-destructive-foreground"
            : "border-border bg-background"
          }
        `}
      >
        {title && <h4 className="text-sm font-medium mb-1">{title}</h4>}
        {description && <p className="text-sm opacity-90">{description}</p>}
        <button
          onClick={() => onOpenChange(false)}
          className="mt-2 text-xs underline opacity-70 hover:opacity-100"
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}
