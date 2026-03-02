"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  getCertificatesGrouped,
  getCertificateViewUrl,
  getCertificateDownloadUrl,
  deleteCertificate,
  bulkDeleteCertificates,
  type CertificateItem,
  type CertificateStatusFilter,
  type GroupedDocument,
} from "@/lib/api";
import { PdfViewerModal } from "@/components/PdfViewerModal";
import { formatDate } from "@/lib/utils";

const FILTERS: { value: CertificateStatusFilter | ""; label: string }[] = [
  { value: "", label: "All" },
  { value: "Valid", label: "Valid" },
  { value: "Expiring Soon", label: "Expiring Soon" },
  { value: "Expired", label: "Expired" },
];

function StatusBadge({ status }: { status: string }) {
  const statusClass =
    status === "Expired"
      ? "bg-red-100 text-red-800"
      : status === "Expiring Soon"
        ? "bg-amber-100 text-amber-800"
        : "bg-emerald-100 text-emerald-800";
  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${statusClass}`}
    >
      {status}
    </span>
  );
}

function ViewIcon({ className }: { className?: string }) {
  return (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}
function DownloadIcon({ className }: { className?: string }) {
  return (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  );
}
function TrashIcon({ className }: { className?: string }) {
  return (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M3 6h18" />
      <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
      <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
      <line x1="10" y1="11" x2="10" y2="17" />
      <line x1="14" y1="11" x2="14" y2="17" />
    </svg>
  );
}

function filterCertificatesByStatus(certs: CertificateItem[], status: CertificateStatusFilter | ""): CertificateItem[] {
  if (!status) return certs;
  return certs.filter((c) => c.status === status);
}

export function DashboardWithFilters() {
  const [statusFilter, setStatusFilter] = useState<CertificateStatusFilter | "">("");
  const [groupedDocs, setGroupedDocs] = useState<GroupedDocument[]>([]);
  const [expandedDocs, setExpandedDocs] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pdfViewUrl, setPdfViewUrl] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const fetchGroupedCertificates = useCallback(() => {
    setLoading(true);
    setError(null);
    getCertificatesGrouped()
      .then(setGroupedDocs)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load certificates"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchGroupedCertificates();
  }, [fetchGroupedCertificates]);

  const toggleDoc = useCallback((documentId: string) => {
    setExpandedDocs((prev) => ({ ...prev, [documentId]: !prev[documentId] }));
  }, []);

  const filteredGroupedDocs = groupedDocs
    .map((doc) => ({
      ...doc,
      certificates: filterCertificatesByStatus(doc.certificates, statusFilter),
    }))
    .filter((doc) => doc.certificates.length > 0);

  const handleView = useCallback(async (certificateId: string) => {
    try {
      const { url } = await getCertificateViewUrl(certificateId);
      setPdfViewUrl(url);
    } catch {
      setError("Failed to open certificate");
    }
  }, []);

  const handleDownload = useCallback(async (certificateId: string) => {
    try {
      const { url } = await getCertificateDownloadUrl(certificateId);
      window.open(url, "_blank", "noopener,noreferrer");
    } catch {
      setError("Failed to download certificate");
    }
  }, []);

  const handleDelete = useCallback(
    async (certificateId: string) => {
      if (!confirm("Delete this certificate? This cannot be undone.")) return;
      setError(null);
      try {
        await deleteCertificate(certificateId);
        setSelectedIds((prev) => {
          const next = new Set(prev);
          next.delete(certificateId);
          return next;
        });
        fetchGroupedCertificates();
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to delete certificate");
      }
    },
    [fetchGroupedCertificates]
  );

  const toggleSelect = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const handleBulkDownload = useCallback(async () => {
    if (selectedIds.size === 0) return;
    setError(null);
    for (const id of Array.from(selectedIds)) {
      try {
        const { url } = await getCertificateDownloadUrl(id);
        window.open(url, "_blank", "noopener,noreferrer");
      } catch {
        setError("Failed to open one or more downloads.");
        break;
      }
    }
  }, [selectedIds]);

  const handleBulkDelete = useCallback(async () => {
    if (selectedIds.size === 0) return;
    if (!confirm(`Delete ${selectedIds.size} certificate(s)? This cannot be undone.`)) return;
    setError(null);
    try {
      await bulkDeleteCertificates(Array.from(selectedIds));
      setSelectedIds(new Set());
      fetchGroupedCertificates();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete certificates");
    }
  }, [selectedIds, fetchGroupedCertificates]);

  const isExpanded = (documentId: string) => expandedDocs[documentId] !== false;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {FILTERS.map(({ value, label }) => (
          <button
            key={value || "all"}
            type="button"
            onClick={() => setStatusFilter(value)}
            className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              statusFilter === value
                ? "bg-slate-800 text-white"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            {label}
          </button>
        ))}
      </div>
      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
          {error}
        </div>
      )}
      {loading ? (
        <div className="py-8 text-center text-sm text-slate-500">Loading certificates…</div>
      ) : filteredGroupedDocs.length === 0 ? (
        <div className="rounded-xl border border-slate-200 bg-slate-50/50 py-12 px-6 text-center">
          <p className="text-slate-700 font-medium">No certificates yet</p>
          <p className="mt-1 text-sm text-slate-500">
            Upload documents from the Compliance Checklist for each requirement.
          </p>
          <Link
            href="/compliance-checklist"
            className="mt-4 inline-block rounded-xl border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50"
          >
            View checklist →
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {selectedIds.size > 0 && (
            <div className="flex items-center justify-between rounded-lg border border-blue-200 bg-blue-50 px-4 py-2">
              <span className="text-sm font-medium text-slate-700">
                {selectedIds.size} selected
              </span>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={handleBulkDownload}
                  className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100"
                >
                  Download Selected
                </button>
                <button
                  type="button"
                  onClick={handleBulkDelete}
                  className="rounded-md border border-red-200 bg-red-50 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-100"
                >
                  Delete Selected
                </button>
              </div>
            </div>
          )}
          {filteredGroupedDocs.map((doc) => (
            <div
              key={doc.document_id}
              className="rounded-lg border border-slate-200 bg-white shadow-sm"
            >
              <div className="rounded-t-lg border-b border-slate-200 bg-slate-50 p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-semibold text-lg text-slate-900">
                      {doc.certificates && doc.certificates.length > 0
                        ? (doc.certificates[0].certificate_name || "Untitled Document")
                        : "Untitled Document"}
                    </div>
                    <div className="mt-0.5 text-sm text-slate-500">
                      Uploaded on {formatDate(doc.upload_date)} • {doc.certificates.length} document{doc.certificates.length !== 1 ? "s" : ""}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => toggleDoc(doc.document_id)}
                    className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100"
                  >
                    {isExpanded(doc.document_id) ? "Collapse" : "Expand"}
                  </button>
                </div>
              </div>
              {isExpanded(doc.document_id) && (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-200">
                    <thead>
                      <tr>
                        <th className="bg-slate-50 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600">
                          Certificate Name
                        </th>
                        <th className="bg-slate-50 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600">
                          Report Number
                        </th>
                        <th className="bg-slate-50 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600">
                          Issue Date
                        </th>
                        <th className="bg-slate-50 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600">
                          Expiry Date
                        </th>
                        <th className="bg-slate-50 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600">
                          Status
                        </th>
                        <th className="bg-slate-50 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      {doc.certificates.map((cert) => (
                        <tr key={cert.id} className="hover:bg-slate-50">
                          <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-900">
                            {cert.certificate_name || cert.report_number || "—"}
                          </td>
                          <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-600">
                            {cert.report_number || "—"}
                          </td>
                          <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-600">
                            {formatDate(cert.issue_date)}
                          </td>
                          <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-600">
                            {formatDate(cert.expiry_date)}
                          </td>
                          <td className="whitespace-nowrap px-4 py-3">
                            <StatusBadge status={cert.status} />
                          </td>
                          <td className="whitespace-nowrap px-4 py-3">
                            <div className="flex items-center justify-end gap-3">
                              <input
                                type="checkbox"
                                checked={selectedIds.has(cert.id)}
                                onChange={() => toggleSelect(cert.id)}
                                className="h-4 w-4 accent-blue-600"
                                aria-label={`Select ${cert.report_number || cert.id}`}
                              />
                              <button
                                type="button"
                                onClick={() => handleView(cert.id)}
                                title="View"
                                className="rounded p-1.5 text-gray-600 hover:bg-slate-100"
                                aria-label="View certificate"
                              >
                                <ViewIcon className="w-4 h-4" />
                              </button>
                              <button
                                type="button"
                                onClick={() => handleDownload(cert.id)}
                                title="Download"
                                className="rounded p-1.5 text-gray-600 hover:bg-slate-100"
                                aria-label="Download certificate"
                              >
                                <DownloadIcon className="w-4 h-4" />
                              </button>
                              <button
                                type="button"
                                onClick={() => handleDelete(cert.id)}
                                title="Delete"
                                className="rounded p-1.5 text-red-500 hover:bg-red-50"
                                aria-label="Delete certificate"
                              >
                                <TrashIcon className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      <PdfViewerModal url={pdfViewUrl} onClose={() => setPdfViewUrl(null)} />
    </div>
  );
}
