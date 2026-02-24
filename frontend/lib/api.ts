import { getToken } from "./auth";

const getBaseUrl = () => process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function authHeaders(): Record<string, string> {
  const token = typeof window !== "undefined" ? getToken() : null;
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

export interface Document {
  id: string;
  filename: string;
  file_path: string;
  s3_url?: string | null;
  document_name: string | null;
  expiry_date: string | null;
  category: string | null;
  reminder_days: number;
  created_at: string;
  updated_at: string;
}

export type DocumentStatusFilter = "all" | "active" | "expiring_soon" | "expired";

export async function getDocuments(status?: DocumentStatusFilter): Promise<Document[]> {
  const base =
    typeof window !== "undefined"
      ? "/api/documents"
      : `${getBaseUrl()}/api/v1/documents`;
  const params = new URLSearchParams();
  if (status && status !== "all") {
    params.set("status", status);
  }
  const url = params.toString() ? `${base}?${params.toString()}` : base;
  const res = await fetch(url, { cache: "no-store", headers: authHeaders() });
  if (res.status === 401) {
    throw new Error("Not authenticated. Please log in.");
  }
  if (!res.ok) {
    throw new Error(`Failed to fetch documents: ${res.status}`);
  }
  const data = await res.json();
  return data;
}

export async function uploadDocument(file: File): Promise<Document> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch("/api/upload", {
    method: "POST",
    body: formData,
    headers: authHeaders(),
  });
  if (res.status === 401) {
    throw new Error("Not authenticated. Please log in.");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const msg = typeof err.detail === "string" ? err.detail : err.detail?.[0]?.msg ?? err.detail ?? `Upload failed: ${res.status}`;
    throw new Error(msg);
  }
  return res.json();
}

export async function deleteDocument(id: string): Promise<void> {
  const url =
    typeof window !== "undefined"
      ? `/api/documents/${id}`
      : `${getBaseUrl()}/api/v1/documents/${id}`;
  const res = await fetch(url, { method: "DELETE", headers: authHeaders() });
  if (res.status === 401) {
    throw new Error("Not authenticated. Please log in.");
  }
  if (res.status === 404) {
    throw new Error("Document not found");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(typeof err.detail === "string" ? err.detail : "Delete failed");
  }
}

// --- Document processing (multi-certificate PDF) & certificates ---

export interface ProcessingStatus {
  job_id: string;
  document_id: string;
  status: string;
  progress: number;
  current_step: string;
  current_page: number;
  total_pages: number;
  total_certificates: number;
  error: string | null;
}

export interface UploadDocumentFileResult {
  filename: string;
  job_id?: string;
  document_id?: string;
  error?: string;
}

export interface UploadDocumentResponse {
  success: boolean;
  files: UploadDocumentFileResult[];
}

/** Legacy single-file response shape (when backend returns one file in files array). */
export interface UploadDocumentSingleResponse {
  job_id: string;
  document_id: string;
  message?: string;
}

export async function uploadDocumentWithProcessing(file: File): Promise<UploadDocumentSingleResponse> {
  const res = await uploadDocumentsWithProcessing([file]);
  const first = res.files[0];
  if (!first?.job_id) throw new Error(first?.error ?? "Upload failed");
  return { job_id: first.job_id, document_id: first.document_id ?? "" };
}

export async function uploadDocumentsWithProcessing(files: File[]): Promise<UploadDocumentResponse> {
  if (files.length === 0) throw new Error("No files selected");
  const formData = new FormData();
  for (const file of files) formData.append("files", file);
  const res = await fetch("/api/upload-document", {
    method: "POST",
    body: formData,
    headers: authHeaders(),
  });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(typeof err.detail === "string" ? err.detail : "Upload failed");
  }
  return res.json();
}

export async function getProcessingStatus(jobId: string): Promise<ProcessingStatus> {
  const base =
    typeof window !== "undefined"
      ? "/api/processing-status"
      : `${getBaseUrl()}/api/v1/processing-status`;
  const res = await fetch(`${base}/${encodeURIComponent(jobId)}`, {
    cache: "no-store",
    headers: authHeaders(),
  });
  if (res.status === 404) throw new Error("Job not found");
  if (!res.ok) throw new Error("Failed to get status");
  return res.json();
}

export interface CertificateItem {
  id: string;
  document_id: string;
  report_number: string | null;
  certificate_name: string | null;
  issue_date: string | null;
  expiry_date: string | null;
  page_number: number | null;
  created_at: string;
  source_document_name: string | null;
  view_url: string | null;
  download_url: string | null;
  status: string;
}

export type CertificateStatusFilter = "Valid" | "Expiring Soon" | "Expired";

export interface CertificatesPaginatedResponse {
  items: CertificateItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface GroupedDocument {
  document_id: string;
  file_name: string;
  document_name?: string | null;
  upload_date: string | null;
  certificates: CertificateItem[];
}

export async function getCertificates(
  opts?: { skip?: number; limit?: number; status?: CertificateStatusFilter }
): Promise<CertificatesPaginatedResponse> {
  const params = new URLSearchParams();
  if (opts?.skip != null) params.set("skip", String(opts.skip));
  if (opts?.limit != null) params.set("limit", String(opts.limit));
  if (opts?.status) params.set("status_filter", opts.status);
  const url = `/api/certificates${params.toString() ? `?${params.toString()}` : ""}`;
  const res = await fetch(url, { cache: "no-store", headers: authHeaders() });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (!res.ok) throw new Error("Failed to fetch certificates");
  return res.json();
}

export async function getCertificatesGrouped(): Promise<GroupedDocument[]> {
  const res = await fetch("/api/certificates/grouped", {
    cache: "no-store",
    headers: authHeaders(),
  });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (!res.ok) throw new Error("Failed to fetch certificates");
  return res.json();
}

export async function getCertificateViewUrl(id: string): Promise<{ url: string }> {
  const res = await fetch(`/api/certificates/${encodeURIComponent(id)}/view-url`, {
    cache: "no-store",
    headers: authHeaders(),
  });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (res.status === 404) throw new Error("Certificate not found");
  if (!res.ok) throw new Error("Failed to get view URL");
  return res.json();
}

export async function getCertificateDownloadUrl(id: string): Promise<{ url: string }> {
  const res = await fetch(`/api/certificates/${encodeURIComponent(id)}/download-url`, {
    cache: "no-store",
    headers: authHeaders(),
  });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (res.status === 404) throw new Error("Certificate not found");
  if (!res.ok) throw new Error("Failed to get download URL");
  return res.json();
}

export async function deleteCertificate(id: string): Promise<void> {
  const res = await fetch(`/api/certificates/${encodeURIComponent(id)}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (res.status === 404) throw new Error("Certificate not found");
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(typeof err.detail === "string" ? err.detail : "Failed to delete certificate");
  }
}

export async function bulkDeleteCertificates(ids: string[]): Promise<{ deleted: number }> {
  const res = await fetch("/api/certificates/bulk-delete", {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ certificate_ids: ids }),
  });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(typeof err.detail === "string" ? err.detail : "Failed to delete certificates");
  }
  return res.json();
}

// --- Locker: upload storage-only document, document view/download ---

export async function uploadLockerDocument(file: File): Promise<{ id: string; filename: string; created_at: string }> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch("/api/upload-locker-document", {
    method: "POST",
    body: formData,
    headers: authHeaders(),
  });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(typeof err.detail === "string" ? err.detail : "Upload failed");
  }
  return res.json();
}

export async function getDocumentViewUrl(id: string): Promise<{ url: string }> {
  const base = typeof window !== "undefined" ? "/api/documents" : `${getBaseUrl()}/api/v1/documents`;
  const res = await fetch(`${base}/${encodeURIComponent(id)}/view-url`, {
    cache: "no-store",
    headers: authHeaders(),
  });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (res.status === 404) throw new Error("Document not found");
  if (!res.ok) throw new Error("Failed to get view URL");
  return res.json();
}

export async function getDocumentDownloadUrl(id: string): Promise<{ url: string }> {
  const base = typeof window !== "undefined" ? "/api/documents" : `${getBaseUrl()}/api/v1/documents`;
  const res = await fetch(`${base}/${encodeURIComponent(id)}/download-url`, {
    cache: "no-store",
    headers: authHeaders(),
  });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (res.status === 404) throw new Error("Document not found");
  if (!res.ok) throw new Error("Failed to get download URL");
  return res.json();
}
