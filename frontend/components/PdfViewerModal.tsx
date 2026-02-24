"use client";

import { useEffect } from "react";

interface PdfViewerModalProps {
  url: string | null;
  onClose: () => void;
}

export function PdfViewerModal({ url, onClose }: PdfViewerModalProps) {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [onClose]);

  if (!url) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="PDF viewer"
    >
      <div
        className="flex h-full max-h-[90vh] w-full max-w-4xl flex-col rounded-lg bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-slate-200 px-4 py-2">
          <span className="text-sm font-medium text-slate-700">Certificate PDF</span>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
            aria-label="Close"
          >
            ✕
          </button>
        </div>
        <div className="min-h-0 flex-1 overflow-hidden">
          <iframe
            src={url}
            title="Certificate PDF"
            className="h-full w-full border-0"
          />
        </div>
      </div>
    </div>
  );
}
