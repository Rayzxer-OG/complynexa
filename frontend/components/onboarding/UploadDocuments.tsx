"use client";

import { useRef, useState } from "react";
import { uploadDocuments } from "@/lib/api";

const ACCEPT = ".pdf,.jpg,.jpeg,.png";
const MAX_FILES = 10;

interface UploadDocumentsProps {
  onComplete?: () => void;
  onSkip?: () => void;
}

export function UploadDocuments({ onComplete, onSkip }: UploadDocumentsProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files ?? []);
    const allowed = selected.filter((f) => {
      const ext = f.name.split(".").pop()?.toLowerCase();
      return ["pdf", "jpg", "jpeg", "png"].includes(ext ?? "");
    });
    setFiles((prev) => [...prev, ...allowed].slice(0, MAX_FILES));
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    setError(null);
    setProgress(20);
    try {
      await uploadDocuments(files);
      setProgress(100);
      setSuccess(true);
      setFiles([]);
      onComplete?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-4">
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        multiple
        onChange={handleSelect}
        className="hidden"
      />
      {files.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-slate-50/50 p-3">
          <p className="mb-2 text-sm font-medium text-slate-700">{files.length} file(s) selected</p>
          <ul className="max-h-32 space-y-1 overflow-y-auto text-xs text-slate-600">
            {files.map((f, i) => (
              <li key={i} className="flex items-center justify-between gap-2">
                <span className="truncate">{f.name}</span>
                <button
                  type="button"
                  onClick={() => removeFile(i)}
                  className="shrink-0 text-red-600 hover:underline"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
      {uploading && (
        <div className="h-2 overflow-hidden rounded-full bg-slate-200">
          <div
            className="h-full bg-slate-700 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
      {success && (
        <p className="text-sm font-medium text-emerald-600">Upload complete.</p>
      )}
      {error && (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={uploading}
          className="rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50 disabled:opacity-50"
        >
          {files.length > 0 ? "Add more" : "Choose files"}
        </button>
        {files.length > 0 && (
          <button
            type="button"
            onClick={handleUpload}
            disabled={uploading}
            className="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow-md hover:bg-slate-800 disabled:opacity-50"
          >
            {uploading ? "Uploading…" : "Upload"}
          </button>
        )}
      </div>
    </div>
  );
}
