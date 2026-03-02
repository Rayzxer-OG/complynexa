import { getToken } from "./auth";

/** Centralized API base URL — all requests go to backend (e.g. port 8000). */
export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function authHeaders(): Record<string, string> {
  const token = typeof window !== "undefined" ? getToken() : null;
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

/** Fetch with full URL logged so Network tab shows requests to backend (e.g. port 8000). */
async function apiFetch(url: string, init?: RequestInit): Promise<Response> {
  if (typeof window !== "undefined") {
    console.log("[API]", url);
  }
  return fetch(url, init);
}

// --- Onboarding: register, organization, upload ---

export interface RegisterBody {
  full_name: string;
  email: string;
  password: string;
  mobile?: string;
}

/** Industry from backend master (for registration dropdown) */
export interface Industry {
  industry_id: string;
  industry_name: string;
  industry_code: string | null;
}

export async function getIndustries(): Promise<Industry[]> {
  const url = `${API_BASE}/api/v1/industries`;
  const res = await apiFetch(url);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(typeof data.detail === "string" ? data.detail : "Failed to load industries");
  }
  return res.json();
}

/** Business type from backend master (for registration dropdown) */
export interface BusinessType {
  business_type_id: string;
  business_type_name: string;
  business_type_code: string | null;
}

export async function getBusinessTypes(): Promise<BusinessType[]> {
  const url = `${API_BASE}/api/v1/business-types`;
  const res = await apiFetch(url);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(typeof data.detail === "string" ? data.detail : "Failed to load business types");
  }
  return res.json();
}

/** Organization/unit payload for combined onboarding. Optional fields default on backend. */
export interface OnboardingOrganization {
  organization_name: string;
  unit_name: string;
  address: string;
  state: string;
  industry_id: string;
  business_type_id?: string;
  employees?: number;
  manufacturing?: boolean;
  electrical_load?: number;
}

/** Admin user payload for combined onboarding */
export interface OnboardingUser {
  full_name: string;
  email: string;
  password: string;
  mobile: string;
  alternate_email?: string;
  alternate_mobile?: string;
}

export interface OnboardingBody {
  organization: OnboardingOrganization;
  user: OnboardingUser;
}

export interface OnboardingResponse {
  organization_id: string;
  unit_id: string;
  access_token: string;
  user: { id: string; email: string; full_name: string };
}

export async function submitOnboarding(body: OnboardingBody): Promise<OnboardingResponse> {
  const url = `${API_BASE}/api/v1/auth/onboarding`;
  const res = await apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (res.status === 400) {
    const data = await res.json().catch(() => ({}));
    throw new Error(typeof data.detail === "string" ? data.detail : "Email already registered");
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(typeof data.detail === "string" ? data.detail : "Onboarding failed");
  }
  return res.json();
}

export async function registerUser(body: RegisterBody): Promise<{ id: string; email: string; full_name: string }> {
  const url = `${API_BASE}/api/v1/auth/register`;
  const res = await apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ full_name: body.full_name, email: body.email, password: body.password }),
  });
  if (res.status === 400) {
    const data = await res.json().catch(() => ({}));
    throw new Error(typeof data.detail === "string" ? data.detail : "Email already registered");
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(typeof data.detail === "string" ? data.detail : "Registration failed");
  }
  return res.json();
}

export interface OrganizationCreateBody {
  organization_name: string;
  unit_name: string;
  address: string;
  state: string;
  industry: string;
  business_type: string;
  employees: number;
  manufacturing: boolean;
  electrical_load: number;
}

export async function createOrganization(body: OrganizationCreateBody): Promise<{ ok: boolean; message?: string; unit_id?: string }> {
  const url = `${API_BASE}/api/v1/organization/create`;
  const res = await apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(typeof data.detail === "string" ? data.detail : "Failed to save organization");
  }
  return res.json();
}

// --- Compliance checklist ---

/** M = Mandatory, C = Conditional, O = Optional */
export type ApplicabilityFlag = "M" | "C" | "O";

/** Shown for conditional (C) items: why this compliance is required (question + user answer). */
export interface RequiredBecause {
  condition_question: string;
  condition_key: string;
  user_response: string;
}

export interface ComplianceChecklistItem {
  compliance_requirement_id: string;
  compliance_name: string;
  description: string | null;
  issuing_authority: string | null;
  status: "pending" | "valid" | "expired" | "uploaded" | "expiring_soon";
  expiry_date: string | null;
  /** M = Mandatory, C = Conditional, O = Optional */
  applicability_flag?: ApplicabilityFlag | string | null;
  /** From uploaded document (OCR); only present when document exists */
  license_number?: string | null;
  /** From uploaded document; only present when document exists */
  issue_date?: string | null;
  /** For conditional items: condition question and user response from backend */
  required_because?: RequiredBecause | null;
}

export async function uploadDocumentForCompliance(
  file: File,
  complianceRequirementId: string,
  unitId: string,
  _expiryDate?: string | null
): Promise<UploadDocumentResponse> {
  return uploadDocumentForComplianceWithProgress(
    file,
    complianceRequirementId,
    unitId,
    undefined
  );
}

/** Upload with optional progress callback (0–100). Uses XHR for upload progress. */
export function uploadDocumentForComplianceWithProgress(
  file: File,
  complianceRequirementId: string,
  unitId: string,
  onProgress?: (percent: number) => void
): Promise<UploadDocumentResponse> {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("compliance_requirement_id", complianceRequirementId);
    formData.append("unit_id", unitId);
    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable && onProgress) {
        const percent = Math.min(100, Math.round((e.loaded / e.total) * 100));
        onProgress(percent);
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status === 401) {
        reject(new Error("Not authenticated. Please log in."));
        return;
      }
      if (xhr.status < 200 || xhr.status >= 300) {
        let detail = "Upload failed";
        try {
          const data = JSON.parse(xhr.responseText || "{}");
          if (typeof data.detail === "string") detail = data.detail;
        } catch {
          // ignore
        }
        reject(new Error(detail));
        return;
      }
      try {
        const data = JSON.parse(xhr.responseText || "{}");
        resolve(data);
      } catch {
        reject(new Error("Invalid response"));
      }
    });

    xhr.addEventListener("error", () => reject(new Error("Upload failed")));
    xhr.addEventListener("abort", () => reject(new Error("Upload cancelled")));

    const uploadUrl = `${API_BASE}/api/v1/upload-document`;
    if (typeof window !== "undefined") console.log("[API]", uploadUrl);
    xhr.open("POST", uploadUrl);
    const token = typeof window !== "undefined" ? getToken() : null;
    if (token) {
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }
    xhr.send(formData);
  });
}

/** OCR extraction result for confirmation form (do not save until user confirms). */
export interface OcrExtractResponse {
  document_name: string | null;
  license_number: string | null;
  issuing_authority: string | null;
  issue_date: string | null;
  expiry_date: string | null;
  unit_name: string | null;
  category: string | null;
}

export async function extractOcrDocument(documentId: string): Promise<OcrExtractResponse> {
  const url = `${API_BASE}/api/v1/documents/${encodeURIComponent(documentId)}/extract-ocr`;
  const res = await apiFetch(url, {
    method: "GET",
    headers: authHeaders(),
  });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (res.status === 404) throw new Error("Document not found");
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(typeof err.detail === "string" ? err.detail : "Extraction failed");
  }
  return res.json();
}

export interface DocumentUpdateBody {
  document_name?: string | null;
  expiry_date?: string | null;
  category?: string | null;
  reminder_days?: number | null;
  unit_id?: string | null;
  compliance_id?: string | null;
  license_number?: string | null;
  issuing_authority?: string | null;
  issue_date?: string | null;
  unit_name?: string | null;
  document_file_reference?: string | null;
}

export async function updateDocument(
  documentId: string,
  body: DocumentUpdateBody
): Promise<Document> {
  const url = `${API_BASE}/api/v1/documents/${encodeURIComponent(documentId)}`;
  const res = await apiFetch(url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (res.status === 404) throw new Error("Document not found");
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(typeof err.detail === "string" ? err.detail : "Update failed");
  }
  return res.json();
}

export async function getComplianceChecklist(unitId: string): Promise<ComplianceChecklistItem[]> {
  const url = `${API_BASE}/api/v1/compliance/checklist/${unitId}`;
  const res = await apiFetch(url, { headers: authHeaders() });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (res.status === 404) throw new Error("Unit not found");
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const profileErr = parseProfileSetupRequired(res, data);
    if (profileErr) throw profileErr;
    throw new Error(typeof data.detail === "string" ? data.detail : "Failed to load checklist");
  }
  return res.json();
}

export interface ConditionalQuestion {
  compliance_requirement_id: string;
  compliance_name: string;
  conditional_question: string;
}

export async function getConditionalQuestions(unitId: string): Promise<ConditionalQuestion[]> {
  if (unitId === undefined || unitId === null || unitId === "") {
    throw new Error("Unit not loaded");
  }
  console.log("Fetching conditional for unit:", unitId);
  const url = `${API_BASE}/api/v1/compliance/conditional-questions/${unitId}`;
  const res = await apiFetch(url, { cache: "no-store", headers: authHeaders() });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (res.status === 404) throw new Error("Unit not found");
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(typeof data.detail === "string" ? data.detail : "Failed to load questions");
  }
  const data = await res.json();
  console.log("Conditional response:", data);
  return data;
}

export async function saveComplianceAttribute(
  unitId: string,
  complianceRequirementId: string,
  applies: boolean
): Promise<{ ok: boolean; count: number }> {
  if (unitId === undefined || unitId === null || unitId === "") {
    throw new Error("Unit not loaded");
  }
  console.log("Saving for unit:", unitId);
  const body = {
    unit_id: unitId,
    attributes: [
      {
        compliance_requirement_id: complianceRequirementId,
        applies,
      },
    ],
  };
  const url = `${API_BASE}/api/v1/compliance/compliance-attributes`;
  const res = await apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (res.status === 404) throw new Error("Unit or compliance not found");
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(typeof data.detail === "string" ? data.detail : "Failed to save answer");
  }
  return res.json();
}

/** Bulk save: POST body { unit_id, attributes: [{ compliance_requirement_id, applies }, ...] }. Uses snake_case only. */
export async function saveComplianceAttributesBulk(
  unitId: string,
  attributes: Array<{ compliance_requirement_id: string; applies: boolean }>
): Promise<{ ok: boolean; count: number }> {
  if (unitId === undefined || unitId === null || unitId === "") {
    throw new Error("Unit not loaded");
  }
  console.log("Saving for unit:", unitId);
  const body = {
    unit_id: unitId,
    attributes: attributes.map((a) => ({
      compliance_requirement_id: a.compliance_requirement_id,
      applies: a.applies,
    })),
  };
  const url = `${API_BASE}/api/v1/compliance/compliance-attributes`;
  const res = await apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (res.status === 404) throw new Error("Unit or compliance not found");
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(typeof data.detail === "string" ? data.detail : "Failed to save answers");
  }
  return res.json();
}

/** Format backend error detail (string or validation array) for display. */
export function formatBackendError(data: { detail?: unknown }): string {
  const d = data.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d) && d.length) {
    return d
      .map((x: { loc?: unknown[]; msg?: string }) => {
        const loc = Array.isArray(x.loc) ? x.loc.join(".") : "";
        return loc ? `${loc}: ${x.msg ?? "Invalid"}` : (x.msg ?? "Invalid");
      })
      .join("; ");
  }
  return "Request failed";
}

/**
 * Save compliance profile for onboarding. POST /api/v1/compliance/compliance-attributes.
 * Bulk payload: { unit_id, attributes: [{ compliance_requirement_id, applies }, ...] }.
 */
export async function saveComplianceProfile(
  unitId: string,
  attributes: Array<{ compliance_requirement_id: string; applies: boolean }>
): Promise<{ ok: boolean; count: number }> {
  if (unitId === undefined || unitId === null || unitId === "") {
    throw new Error("Unit not loaded");
  }
  // Ensure bulk shape: backend expects { unit_id, attributes: [...] }, not a single item
  const attributesList = Array.isArray(attributes) ? attributes : [];
  const payload = {
    unit_id: unitId,
    attributes: attributesList
      .filter(
        (a): a is { compliance_requirement_id: string; applies: boolean } =>
          a != null &&
          typeof a === "object" &&
          typeof (a as { compliance_requirement_id?: unknown }).compliance_requirement_id === "string" &&
          typeof (a as { applies?: unknown }).applies === "boolean"
      )
      .map((a) => ({
        compliance_requirement_id: String(a.compliance_requirement_id),
        applies: Boolean(a.applies),
      })),
  };
  const url = `${API_BASE}/api/v1/compliance/compliance-attributes`;
  console.log("Submitting to:", url, payload);
  const res = await apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (res.status === 404) throw new Error("Unit not found");
  if (!res.ok) {
    throw new Error(formatBackendError(data));
  }
  return data;
}

export interface UnitInfo {
  organization_name: string;
  unit_name: string;
  address: string;
  state: string;
  industry?: string | null;
  employee_count?: number;
  hazardous_flag?: boolean;
  boiler_flag?: boolean;
  electrical_load?: number;
  built_up_area?: number;
  spcb_category?: string | null;
  /** Must be true to access dashboard, checklist, risk score. */
  compliance_profile_completed?: boolean;
}

/** Response from GET /units/{unit_id}/activation-status */
export interface ActivationStatus {
  registration_completed: boolean;
  compliance_profile_completed: boolean;
  compliance_matrix_generated: boolean;
  monitoring_active: boolean;
}

export async function getActivationStatus(unitId: string): Promise<ActivationStatus> {
  const url = `${API_BASE}/api/v1/units/${encodeURIComponent(unitId)}/activation-status`;
  const res = await apiFetch(url, { cache: "no-store", headers: authHeaders() });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (res.status === 404) throw new Error("Unit not found");
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(typeof data.detail === "string" ? data.detail : "Failed to load activation status");
  }
  return res.json();
}

/** Thrown when backend returns 403 with code PROFILE_SETUP_REQUIRED. */
export interface ProfileSetupRequiredError {
  code: "PROFILE_SETUP_REQUIRED";
  message: string;
}

export function isProfileSetupRequiredError(e: unknown): e is ProfileSetupRequiredError {
  return typeof e === "object" && e !== null && "code" in e && (e as ProfileSetupRequiredError).code === "PROFILE_SETUP_REQUIRED";
}

export interface UnitUpdatePayload {
  industry?: string;
  employee_count?: number;
  hazardous_flag?: boolean;
  boiler_flag?: boolean;
  electrical_load?: number;
  built_up_area?: number;
  spcb_category?: string | null;
}

function parseProfileSetupRequired(res: Response, data: { detail?: { code?: string; message?: string } }): ProfileSetupRequiredError | null {
  if (res.status !== 403 || typeof data.detail !== "object" || data.detail?.code !== "PROFILE_SETUP_REQUIRED") return null;
  return { code: "PROFILE_SETUP_REQUIRED", message: data.detail.message ?? "Complete Compliance Profile Setup to activate compliance monitoring." };
}

export async function getUnit(unitId: string): Promise<UnitInfo> {
  const url = `${API_BASE}/api/v1/units/${encodeURIComponent(unitId)}`;
  const res = await apiFetch(url, { cache: "no-store", headers: authHeaders() });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (res.status === 404) throw new Error("Unit not found");
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const profileErr = parseProfileSetupRequired(res, data);
    if (profileErr) throw profileErr;
    throw new Error(typeof data.detail === "string" ? data.detail : "Failed to load unit");
  }
  return res.json();
}

export async function updateUnit(
  unitId: string,
  payload: UnitUpdatePayload
): Promise<{ ok: boolean; unit_id: string; compliance_recalculated: boolean; recalc: { added: number; marked_inactive: number } }> {
  const url = `${API_BASE}/api/v1/units/${unitId}`;
  const res = await apiFetch(url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(payload),
  });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (res.status === 404) throw new Error("Unit not found");
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(typeof data.detail === "string" ? data.detail : "Failed to update unit");
  }
  return res.json();
}

export const ESCALATION_TRIGGER_OPTIONS = [
  { value: "7_days_before_expiry", label: "7 days before expiry" },
  { value: "3_days_before_expiry", label: "3 days before expiry" },
  { value: "on_expiry", label: "On expiry" },
] as const;

/** Multi-level escalation: days before expiry when contact is notified (30→L1, 15→L1, 7→L2, 3→L2, 0→L3). */
export const ESCALATION_TRIGGER_DAYS_OPTIONS = [
  { value: 30, label: "30 days before expiry (Level 1)" },
  { value: 15, label: "15 days before expiry (Level 1)" },
  { value: 7, label: "7 days before expiry (Level 2)" },
  { value: 3, label: "3 days before expiry (Level 2)" },
  { value: 0, label: "On expiry (Level 3)" },
] as const;

export type EscalationTriggerValue = (typeof ESCALATION_TRIGGER_OPTIONS)[number]["value"];

export interface EscalationContactInput {
  level: 1 | 2 | 3;
  name: string;
  email: string;
  mobile: string | null;
  /** Preferred: 30, 15, 7, 3, or 0. Backward compat: escalation_trigger. */
  escalation_trigger_days?: number | null;
  escalation_trigger?: EscalationTriggerValue;
}

export interface EscalationContactResponse {
  level: number;
  name: string;
  email: string;
  mobile: string | null;
  escalation_trigger: string;
  escalation_trigger_days?: number | null;
}

export async function getEscalationContacts(unitId: string): Promise<EscalationContactResponse[]> {
  const url = `${API_BASE}/api/v1/units/${unitId}/escalation-contacts`;
  const res = await apiFetch(url, { cache: "no-store", headers: authHeaders() });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (res.status === 404) throw new Error("Unit not found");
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(typeof data.detail === "string" ? data.detail : "Failed to load escalation contacts");
  }
  return res.json();
}

export async function saveEscalationContacts(
  unitId: string,
  contacts: EscalationContactInput[]
): Promise<{ ok: boolean; count: number }> {
  const url = `${API_BASE}/api/v1/units/${unitId}/escalation-contacts`;
  const res = await apiFetch(url, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ contacts }),
  });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (res.status === 404) throw new Error("Unit not found");
  if (res.status === 400) {
    const data = await res.json().catch(() => ({}));
    throw new Error(typeof data.detail === "string" ? data.detail : "Invalid escalation contacts");
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(typeof data.detail === "string" ? data.detail : "Failed to save");
  }
  return res.json();
}

export interface ComplianceDocumentResponse {
  id: string;
  filename: string;
  document_name: string | null;
  expiry_date: string | null;
  created_at: string;
}

export async function getComplianceDocument(complianceRequirementId: string): Promise<ComplianceDocumentResponse> {
  const url = `${API_BASE}/api/v1/compliance/document/${encodeURIComponent(complianceRequirementId)}`;
  const res = await apiFetch(url, { headers: authHeaders() });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (!res.ok) throw new Error("Document not found");
  return res.json();
}

export async function uploadDocuments(files: File[]): Promise<UploadDocumentResponse> {
  return uploadDocumentsWithProcessing(files);
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
  const params = new URLSearchParams();
  if (status && status !== "all") {
    params.set("status", status);
  }
  const url = params.toString() ? `${API_BASE}/api/v1/documents?${params.toString()}` : `${API_BASE}/api/v1/documents`;
  const res = await apiFetch(url, { cache: "no-store", headers: authHeaders() });
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
  const url = `${API_BASE}/api/v1/documents`;
  const res = await apiFetch(url, {
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
  const url = `${API_BASE}/api/v1/documents/${id}`;
  const res = await apiFetch(url, { method: "DELETE", headers: authHeaders() });
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
  const url = `${API_BASE}/api/v1/upload-document`;
  const res = await apiFetch(url, {
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
  const url = `${API_BASE}/api/v1/processing-status/${encodeURIComponent(jobId)}`;
  const res = await apiFetch(url, {
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
  const url = `${API_BASE}/api/v1/certificates${params.toString() ? `?${params.toString()}` : ""}`;
  const res = await apiFetch(url, { cache: "no-store", headers: authHeaders() });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (!res.ok) throw new Error("Failed to fetch certificates");
  return res.json();
}

export async function getCertificatesGrouped(): Promise<GroupedDocument[]> {
  const url = `${API_BASE}/api/v1/certificates/grouped`;
  const res = await apiFetch(url, {
    cache: "no-store",
    headers: authHeaders(),
  });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (!res.ok) throw new Error("Failed to fetch certificates");
  return res.json();
}

export async function getCertificateViewUrl(id: string): Promise<{ url: string }> {
  const url = `${API_BASE}/api/v1/certificates/${encodeURIComponent(id)}/view-url`;
  const res = await apiFetch(url, {
    cache: "no-store",
    headers: authHeaders(),
  });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (res.status === 404) throw new Error("Certificate not found");
  if (!res.ok) throw new Error("Failed to get view URL");
  return res.json();
}

export async function getCertificateDownloadUrl(id: string): Promise<{ url: string }> {
  const url = `${API_BASE}/api/v1/certificates/${encodeURIComponent(id)}/download-url`;
  const res = await apiFetch(url, {
    cache: "no-store",
    headers: authHeaders(),
  });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (res.status === 404) throw new Error("Certificate not found");
  if (!res.ok) throw new Error("Failed to get download URL");
  return res.json();
}

export async function deleteCertificate(id: string): Promise<void> {
  const url = `${API_BASE}/api/v1/certificates/${encodeURIComponent(id)}`;
  const res = await apiFetch(url, {
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
  const url = `${API_BASE}/api/v1/certificates/bulk-delete`;
  const res = await apiFetch(url, {
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
  const url = `${API_BASE}/api/v1/upload-locker-document`;
  const res = await apiFetch(url, {
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
  const url = `${API_BASE}/api/v1/documents/${encodeURIComponent(id)}/view-url`;
  const res = await apiFetch(url, {
    cache: "no-store",
    headers: authHeaders(),
  });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (res.status === 404) throw new Error("Document not found");
  if (!res.ok) throw new Error("Failed to get view URL");
  return res.json();
}

export async function getDocumentDownloadUrl(id: string): Promise<{ url: string }> {
  const url = `${API_BASE}/api/v1/documents/${encodeURIComponent(id)}/download-url`;
  const res = await apiFetch(url, {
    cache: "no-store",
    headers: authHeaders(),
  });
  if (res.status === 401) throw new Error("Not authenticated. Please log in.");
  if (res.status === 404) throw new Error("Document not found");
  if (!res.ok) throw new Error("Failed to get download URL");
  return res.json();
}
