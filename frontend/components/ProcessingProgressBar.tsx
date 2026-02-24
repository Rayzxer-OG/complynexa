"use client";

import type { ProcessingStatus } from "@/lib/api";

interface ProcessingProgressBarProps {
  status: ProcessingStatus | null;
}

export function ProcessingProgressBar({ status }: ProcessingProgressBarProps) {
  if (!status || status.status === "completed" || status.status === "failed") {
    return null;
  }

  const stepLabel = status.current_step;

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="font-medium text-slate-700">{stepLabel}</span>
        <span className="text-slate-500">{status.progress}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
        <div
          className="h-full rounded-full bg-blue-600 transition-all duration-300"
          style={{ width: `${Math.min(100, status.progress)}%` }}
        />
      </div>
      <p className="mt-2 text-xs text-slate-500">
        Powered by AWS Textract (OCR) & AI extraction
      </p>
      {status.total_certificates > 0 && (
        <p className="mt-0.5 text-xs text-slate-500">
          Documents found: {status.total_certificates}
        </p>
      )}
    </div>
  );
}
