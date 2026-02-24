"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  getProcessingStatus,
  uploadDocumentsWithProcessing,
  type ProcessingStatus,
  type UploadDocumentFileResult,
} from "@/lib/api";
import { ProcessingProgressBar } from "@/components/ProcessingProgressBar";

const POLL_INTERVAL_MS = 1500;

type FileItemStatus = "pending" | "uploading" | "processing" | "done" | "error";

interface FileItem {
  file: File;
  status: FileItemStatus;
  jobId: string | null;
  statusData: ProcessingStatus | null;
  error: string | null;
}

export function UploadForm() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [fileItems, setFileItems] = useState<FileItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const chosen = e.target.files;
    if (!chosen?.length) return;
    const newItems: FileItem[] = Array.from(chosen).map((file) => ({
      file,
      status: "pending" as const,
      jobId: null,
      statusData: null,
      error: null,
    }));
    setFileItems((prev) => [...prev, ...newItems]);
    setError(null);
    e.target.value = "";
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files;
    if (!dropped?.length) return;
    const newItems: FileItem[] = Array.from(dropped).map((file) => ({
      file,
      status: "pending" as const,
      jobId: null,
      statusData: null,
      error: null,
    }));
    setFileItems((prev) => [...prev, ...newItems]);
    setError(null);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  const removeFile = useCallback((index: number) => {
    setFileItems((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const jobIds = fileItems.filter((item) => item.jobId).map((item) => item.jobId!);
  const hasActiveJobs = jobIds.length > 0 && fileItems.some((item) => item.status === "processing" || item.status === "uploading");

  useEffect(() => {
    if (jobIds.length === 0) return;
    const t = setInterval(async () => {
      for (const jobId of jobIds) {
        try {
          const status = await getProcessingStatus(jobId);
          setFileItems((prev) =>
            prev.map((item) =>
              item.jobId === jobId
                ? {
                    ...item,
                    status: status.status === "completed" ? "done" : status.status === "failed" ? "error" : "processing",
                    statusData: status,
                    error: status.status === "failed" ? (status.error ?? "Processing failed") : null,
                  }
                : item
            )
          );
        } catch {
          // keep current state
        }
      }
    }, POLL_INTERVAL_MS);
    return () => clearInterval(t);
  }, [jobIds.join(",")]);

  useEffect(() => {
    if (fileItems.length === 0) return;
    const allDone = fileItems.every((item) => item.status === "done" || item.status === "error");
    if (allDone) {
      setUploading(false);
      const atLeastOneSuccess = fileItems.some((item) => item.status === "done");
      if (atLeastOneSuccess) {
        router.push("/dashboard");
        router.refresh();
      }
    }
  }, [fileItems, router]);

  const uploadFiles = async () => {
    const pending = fileItems.filter((item) => item.status === "pending");
    if (pending.length === 0) {
      setError("No files to upload. Add files first.");
      return;
    }
    setError(null);
    setUploading(true);
    setFileItems((prev) =>
      prev.map((item) => (item.status === "pending" ? { ...item, status: "uploading" as const } : item))
    );
    try {
      const filesToUpload = pending.map((item) => item.file);
      const res = await uploadDocumentsWithProcessing(filesToUpload);
      const byFilename: Record<string, UploadDocumentFileResult> = {};
      for (const f of res.files) byFilename[f.filename] = f;

      setFileItems((prev) =>
        prev.map((item) => {
          const result = byFilename[item.file.name];
          if (!result) return item;
          if (result.error) {
            return { ...item, status: "error" as const, error: result.error };
          }
          return {
            ...item,
            status: "processing" as const,
            jobId: result.job_id ?? null,
            statusData: null,
          };
        })
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
      setFileItems((prev) =>
        prev.map((item) => (item.status === "uploading" ? { ...item, status: "pending" as const } : item))
      );
      setUploading(false);
    }
  };

  const statusLabel = (item: FileItem): string => {
    switch (item.status) {
      case "pending":
        return "Ready";
      case "uploading":
        return "Uploading…";
      case "processing":
        return item.statusData ? `${item.statusData.progress}%` : "Processing…";
      case "done":
        return "Done";
      case "error":
        return item.error ?? "Error";
      default:
        return "Ready";
    }
  };

  return (
    <form className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm" onSubmit={(e) => e.preventDefault()}>
      <div className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">
            Select or drop files (PDF, images, DOCX, etc.)
          </label>
          <input
            ref={inputRef}
            id="file-upload"
            type="file"
            multiple
            accept=".pdf,.png,.jpg,.jpeg,.webp,.tiff,.bmp,.docx,.doc,.xlsx,.xls,.txt"
            onChange={handleFileSelect}
            className="hidden"
          />
          <div
            role="button"
            tabIndex={0}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onClick={() => inputRef.current?.click()}
            onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
            className="cursor-pointer rounded-lg border-2 border-dashed border-slate-300 p-8 text-center transition-colors hover:border-slate-400 hover:bg-slate-50/50"
          >
            <p className="font-medium text-slate-700">Drag and drop files here</p>
            <p className="mt-1 text-sm text-slate-500">or click to select multiple files</p>
          </div>
        </div>

        {fileItems.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium text-slate-700">Files ({fileItems.length})</p>
            <ul className="divide-y divide-slate-200 rounded-md border border-slate-200">
              {fileItems.map((item, index) => (
                <li
                  key={`${item.file.name}-${index}`}
                  className="flex items-center justify-between px-3 py-2 text-sm"
                >
                  <span className="truncate text-slate-900">{item.file.name}</span>
                  <span className="flex shrink-0 items-center gap-2">
                    <span
                      className={
                        item.status === "error"
                          ? "text-red-600"
                          : item.status === "done"
                            ? "text-emerald-600"
                            : "text-slate-500"
                      }
                    >
                      {statusLabel(item)}
                    </span>
                    {item.status === "pending" && (
                      <button
                        type="button"
                        onClick={() => removeFile(index)}
                        className="text-slate-400 hover:text-red-600"
                        aria-label={`Remove ${item.file.name}`}
                      >
                        ×
                      </button>
                    )}
                  </span>
                </li>
              ))}
            </ul>
            {fileItems.some((i) => i.status === "processing" && i.statusData) && (
              <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
                <ProcessingProgressBar
                  status={fileItems.find((i) => i.status === "processing")?.statusData ?? null}
                />
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
            {error}
          </div>
        )}

        <div className="flex gap-3">
          <button
            type="button"
            onClick={uploadFiles}
            disabled={uploading || fileItems.length === 0}
            className="rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {uploading ? "Processing…" : "Upload All"}
          </button>
          <a
            href="/dashboard"
            className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Cancel
          </a>
        </div>
      </div>
    </form>
  );
}
