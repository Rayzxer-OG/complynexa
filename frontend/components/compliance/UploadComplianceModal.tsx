"use client";

import { useRef, useState, useEffect } from "react";
import {
  uploadDocumentForComplianceWithProgress,
  extractOcrDocument,
  updateDocument,
  getDocumentViewUrl,
  type OcrExtractResponse,
} from "@/lib/api";
import { formatDateDDMMYYYY } from "@/lib/utils";

interface UploadComplianceModalProps {
  open: boolean;
  onClose: () => void;
  complianceName: string;
  complianceRequirementId: string;
  unitId: string;
  onSuccess?: () => void;
}

const ACCEPT = ".pdf,.jpg,.jpeg,.png";
const ALLOWED_EXTENSIONS = ["pdf", "jpg", "jpeg", "png"];
const CATEGORIES = ["License", "Insurance", "Contract", "Compliance", "Other"];

function isAllowedFile(file: File): boolean {
  const ext = file.name.split(".").pop()?.toLowerCase();
  return !!ext && ALLOWED_EXTENSIONS.includes(ext);
}

function isPdfFile(file: File): boolean {
  return file.name.toLowerCase().endsWith(".pdf");
}

function toFormState(extracted: OcrExtractResponse | null) {
  return {
    document_name: extracted?.document_name ?? "",
    license_number: extracted?.license_number ?? "",
    issuing_authority: extracted?.issuing_authority ?? "",
    issue_date: extracted?.issue_date ?? "",
    expiry_date: extracted?.expiry_date ?? "",
    unit_name: extracted?.unit_name ?? "",
    category: extracted?.category ?? "",
  };
}

export function UploadComplianceModal({
  open,
  onClose,
  complianceName,
  complianceRequirementId,
  unitId,
  onSuccess,
}: UploadComplianceModalProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [step, setStep] = useState<"upload" | "processing" | "confirm">("upload");
  const [file, setFile] = useState<File | null>(null);
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingMessage, setProcessingMessage] = useState("");
  const [extractError, setExtractError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [form, setForm] = useState(toFormState(null));
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [showExpiryConfirmModal, setShowExpiryConfirmModal] = useState(false);
  const analyzingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const setFileAndClearError = (f: File | null) => {
    setFile(f);
    setError(null);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f && !isAllowedFile(f)) {
      setError("Only PDF, JPG, and PNG are supported");
      return;
    }
    setFileAndClearError(f ?? null);
    e.target.value = "";
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    const dropped = e.dataTransfer.files?.[0];
    if (!dropped) return;
    if (!isAllowedFile(dropped)) {
      setError("Only PDF, JPG, and PNG are supported");
      return;
    }
    setFileAndClearError(dropped);
  };

  useEffect(() => {
    return () => {
      if (analyzingTimeoutRef.current) clearTimeout(analyzingTimeoutRef.current);
    };
  }, []);

  useEffect(() => {
    if (step !== "confirm" || !documentId) {
      setPreviewUrl(null);
      setPreviewError(null);
      return;
    }
    let cancelled = false;
    setPreviewLoading(true);
    setPreviewError(null);
    getDocumentViewUrl(documentId)
      .then(({ url }) => {
        if (!cancelled) {
          setPreviewUrl(url);
          setPreviewError(null);
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setPreviewError(e instanceof Error ? e.message : "Preview unavailable");
          setPreviewUrl(null);
        }
      })
      .finally(() => {
        if (!cancelled) setPreviewLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [step, documentId]);

  const handleUpload = async () => {
    if (!file) {
      setError("Choose a file first");
      return;
    }
    setError(null);
    setExtractError(null);
    setLoading(true);
    setStep("processing");
    setUploadProgress(0);
    setProcessingMessage("Uploading document...");
    try {
      const res = await uploadDocumentForComplianceWithProgress(
        file,
        complianceRequirementId,
        unitId,
        (percent) => {
          setUploadProgress(percent);
        }
      );
      const first = res.files?.[0];
      const id = first?.document_id ?? (res as { document_id?: string }).document_id;
      if (!id) {
        setError("Upload succeeded but no document ID returned");
        setLoading(false);
        setStep("upload");
        return;
      }
      setDocumentId(id);
      setUploadProgress(100);
      setForm(toFormState(null));
      setExtractError(null);
      setProcessingMessage("Extracting compliance data...");
      analyzingTimeoutRef.current = setTimeout(() => {
        setProcessingMessage("Analyzing document...");
      }, 1500);
      try {
        const extracted = await extractOcrDocument(id);
        if (analyzingTimeoutRef.current) {
          clearTimeout(analyzingTimeoutRef.current);
          analyzingTimeoutRef.current = null;
        }
        setForm(toFormState(extracted));
        setProcessingMessage("Extraction complete");
        await new Promise((r) => setTimeout(r, 800));
        setStep("confirm");
      } catch (e) {
        if (analyzingTimeoutRef.current) {
          clearTimeout(analyzingTimeoutRef.current);
          analyzingTimeoutRef.current = null;
        }
        setExtractError(e instanceof Error ? e.message : "Could not extract data from document. Please enter details manually.");
        setForm(toFormState(null));
        setProcessingMessage("Extraction complete");
        await new Promise((r) => setTimeout(r, 600));
        setStep("confirm");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
      setStep("upload");
    } finally {
      setLoading(false);
      setUploadProgress(0);
      setProcessingMessage("");
    }
  };

  const doSave = async () => {
    if (!documentId) return;
    const expiry = form.expiry_date.trim();
    if (!expiry) {
      setError("Expiry date is required for reminders.");
      return;
    }
    setError(null);
    setLoading(true);
    setShowExpiryConfirmModal(false);
    try {
      await updateDocument(documentId, {
        unit_id: unitId,
        compliance_id: complianceRequirementId,
        document_name: form.document_name.trim() || undefined,
        license_number: form.license_number.trim() || undefined,
        issuing_authority: form.issuing_authority.trim() || undefined,
        issue_date: form.issue_date.trim() || undefined,
        expiry_date: expiry,
        unit_name: form.unit_name.trim() || undefined,
        category: form.category.trim() || undefined,
        document_file_reference: documentId,
      });
      onSuccess?.();
      handleClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save");
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmClick = () => {
    const expiry = form.expiry_date.trim();
    if (!expiry) {
      setError("Expiry date is required for reminders.");
      return;
    }
    setError(null);
    setShowExpiryConfirmModal(true);
  };

  const handleClose = () => {
    setStep("upload");
    setFile(null);
    setDocumentId(null);
    setUploadProgress(0);
    setProcessingMessage("");
    setPreviewUrl(null);
    setPreviewError(null);
    setShowExpiryConfirmModal(false);
    setForm(toFormState(null));
    setError(null);
    setExtractError(null);
    onClose();
  };

  const updateForm = (field: keyof typeof form, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setError(null);
  };

  if (!open) return null;

  if (step === "processing") {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        <div className="absolute inset-0 bg-slate-900/50" onClick={() => {}} aria-hidden />
        <div className="relative z-10 w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-xl">
          <h3 className="text-lg font-semibold text-slate-900">Processing document</h3>
          <p className="mt-1 text-sm text-slate-600">
            For: <strong>{complianceName}</strong>
          </p>
          <div className="mt-6 space-y-4">
            {uploadProgress < 100 && (
              <div>
                <div className="flex justify-between text-xs text-slate-500 mb-1">
                  <span>Uploading</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-200 overflow-hidden">
                  <div
                    className="h-full bg-slate-700 transition-[width] duration-300 ease-out"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}
            <div className="flex items-center gap-3 text-slate-700">
              <svg
                className="animate-spin h-5 w-5 text-slate-600 flex-shrink-0"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                aria-hidden
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              <span className="text-sm font-medium">{processingMessage}</span>
            </div>
          </div>
          {error && (
            <p className="mt-4 text-sm text-red-600" role="alert">
              {error}
            </p>
          )}
        </div>
      </div>
    );
  }

  if (step === "confirm") {
    const showPdfPreview = file && isPdfFile(file);
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="absolute inset-0 bg-slate-900/50" onClick={handleClose} aria-hidden />
        <div className="relative z-10 w-full max-w-5xl rounded-xl border border-slate-200 bg-white shadow-xl max-h-[90vh] overflow-hidden flex flex-col">
          {/* Expiry date confirmation safeguard modal */}
          {showExpiryConfirmModal && (
            <div className="absolute inset-0 z-20 flex items-center justify-center bg-slate-900/40 rounded-xl">
              <div
                className="mx-4 w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-xl"
                role="dialog"
                aria-labelledby="expiry-confirm-title"
                aria-modal="true"
              >
                <h4 id="expiry-confirm-title" className="text-base font-semibold text-slate-900">
                  Confirm expiry date
                </h4>
                <p className="mt-3 text-sm text-slate-600">
                  Please confirm that the expiry date is correct. Incorrect expiry date will cause incorrect compliance reminders.
                </p>
                <p className="mt-2 text-sm font-medium text-slate-700">
                  Expiry date: <span className="text-slate-900">{formatDateDDMMYYYY(form.expiry_date || null)}</span>
                </p>
                <div className="mt-6 flex flex-wrap gap-3 justify-end">
                  <button
                    type="button"
                    onClick={() => setShowExpiryConfirmModal(false)}
                    className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                  >
                    Edit expiry date
                  </button>
                  <button
                    type="button"
                    onClick={doSave}
                    disabled={loading}
                    className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
                  >
                    {loading ? "Saving…" : "Confirm expiry date"}
                  </button>
                </div>
              </div>
            </div>
          )}
          <div className="px-6 py-4 border-b border-slate-200 flex-shrink-0">
            <h3 className="text-lg font-semibold text-slate-900">Verify extracted information</h3>
            <p className="mt-1 text-sm text-slate-600">
              For: <strong>{complianceName}</strong>
            </p>
            <p className="mt-2 text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
              Please verify extracted information before saving.
            </p>
            {extractError && (
              <p className="mt-2 text-sm text-amber-700" role="alert">
                {extractError}
              </p>
            )}
          </div>
          <div className="flex-1 overflow-y-auto">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
              {/* Document preview */}
              <div className="flex flex-col min-h-0">
                <h4 className="text-sm font-semibold text-slate-700 mb-2">Document preview</h4>
                <div className="rounded-lg border border-slate-200 bg-slate-50 flex-1 min-h-[240px] max-h-[50vh] flex items-center justify-center overflow-hidden">
                  {previewLoading && (
                    <div className="flex flex-col items-center gap-2 text-slate-500">
                      <svg
                        className="animate-spin h-8 w-8 text-slate-400"
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        aria-hidden
                      >
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      <span className="text-xs">Loading preview…</span>
                    </div>
                  )}
                  {previewError && !previewLoading && (
                    <p className="text-sm text-slate-500 px-4 text-center">{previewError}</p>
                  )}
                  {previewUrl && !previewLoading && showPdfPreview && (
                    <iframe
                      src={previewUrl}
                      title="Document preview"
                      className="w-full h-full min-h-[280px] rounded-lg border-0"
                    />
                  )}
                  {previewUrl && !previewLoading && file && !isPdfFile(file) && (
                    <div className="w-full h-full min-h-[280px] flex items-center justify-center p-2">
                      <img
                        src={previewUrl}
                        alt="Document preview"
                        className="max-w-full max-h-full object-contain rounded"
                      />
                    </div>
                  )}
                </div>
              </div>
              {/* Extracted form */}
              <div>
                <h4 className="text-sm font-semibold text-slate-700 mb-3">Extracted data</h4>
                <div className="space-y-3">
            <div>
              <label className="mb-0.5 block text-sm font-medium text-slate-700">Document name</label>
              <input
                type="text"
                value={form.document_name}
                onChange={(e) => updateForm("document_name", e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="mb-0.5 block text-sm font-medium text-slate-700">License number</label>
              <input
                type="text"
                value={form.license_number}
                onChange={(e) => updateForm("license_number", e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="mb-0.5 block text-sm font-medium text-slate-700">Issuing authority</label>
              <input
                type="text"
                value={form.issuing_authority}
                onChange={(e) => updateForm("issuing_authority", e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="mb-0.5 block text-sm font-medium text-slate-700">Issue date</label>
              <input
                type="date"
                value={form.issue_date}
                onChange={(e) => updateForm("issue_date", e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="mb-0.5 block text-sm font-medium text-slate-700">
                Expiry date <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                value={form.expiry_date}
                onChange={(e) => updateForm("expiry_date", e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="mb-0.5 block text-sm font-medium text-slate-700">Unit name</label>
              <input
                type="text"
                value={form.unit_name}
                onChange={(e) => updateForm("unit_name", e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="mb-0.5 block text-sm font-medium text-slate-700">Category</label>
              <select
                value={form.category}
                onChange={(e) => updateForm("category", e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              >
                <option value="">Select...</option>
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
                </div>
              </div>
            </div>
          </div>
          <div className="px-6 py-4 border-t border-slate-200 flex-shrink-0 bg-slate-50/50">
            {error && (
              <p className="mb-3 text-sm text-red-600" role="alert">
                {error}
              </p>
            )}
            <div className="flex justify-between">
              <button
                type="button"
                onClick={() => { setStep("upload"); setDocumentId(null); setExtractError(null); setError(null); setPreviewUrl(null); setPreviewError(null); setShowExpiryConfirmModal(false); }}
                className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Change file
              </button>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={handleClose}
                  className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleConfirmClick}
                  disabled={loading || !form.expiry_date.trim()}
                  className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
                >
                  {loading ? "Saving…" : "Confirm"}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-slate-900/50" onClick={handleClose} aria-hidden />
      <div className="relative z-10 w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-xl">
        <h3 className="text-lg font-semibold text-slate-900">Upload document</h3>
        <p className="mt-1 text-sm text-slate-600">
          For: <strong>{complianceName}</strong>
        </p>
        <p className="mt-2 text-xs text-slate-500">PDF, JPG, or PNG. You will verify extracted details before saving.</p>

        <div className="mt-4 space-y-4">
          <div>
            <input
              ref={inputRef}
              type="file"
              accept={ACCEPT}
              onChange={handleFileChange}
              className="hidden"
            />
            <div
              role="button"
              tabIndex={0}
              onClick={() => inputRef.current?.click()}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  inputRef.current?.click();
                }
              }}
              onDragEnter={handleDragEnter}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`w-full rounded-xl border-2 border-dashed px-4 py-6 text-center transition-colors ${
                isDragOver
                  ? "border-slate-500 bg-slate-100"
                  : "border-slate-300 bg-slate-50 hover:border-slate-400 hover:bg-slate-100"
              }`}
              aria-label="Drop file here or click to choose"
            >
              <p className="text-sm font-medium text-slate-700">
                {isDragOver ? "Drop file here" : "Drag and drop file here, or click to choose"}
              </p>
              <p className="mt-1 text-xs text-slate-500">PDF, JPG, or PNG</p>
            </div>
            {file && (
              <p className="mt-2 text-sm text-slate-600">
                Selected: {file.name}
              </p>
            )}
          </div>
        </div>

        {error && (
          <p className="mt-2 text-sm text-red-600" role="alert">
            {error}
          </p>
        )}

        <div className="mt-6 flex justify-end gap-2">
          <button
            type="button"
            onClick={handleClose}
            className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleUpload}
            disabled={loading || !file}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
          >
            {loading ? "Uploading…" : "Upload"}
          </button>
        </div>
      </div>
    </div>
  );
}
