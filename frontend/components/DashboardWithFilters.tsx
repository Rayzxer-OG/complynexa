"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getCertificatesGrouped,
  getCertificateViewUrl,
  getCertificateDownloadUrl,
  deleteDocument,
  type CertificateItem,
  type GroupedDocument,
} from "@/lib/api";
import { PdfViewerModal } from "@/components/PdfViewerModal";

function formatDate(s: string | null): string {
  if (!s) return "—";
  try {
    const d = new Date(s);
    return d.toLocaleDateString();
  } catch {
    return s;
  }
}

function getEarliestExpiry(certificates: CertificateItem[]): string {
  const dates = certificates
    .map((c) => c.expiry_date)
    .filter((d): d is string => !!d);
  if (dates.length === 0) return "—";
  const earliest = dates.sort((a, b) => new Date(a).getTime() - new Date(b).getTime())[0];
  return formatDate(earliest);
}

export function DashboardWithFilters() {
  const [groupedDocs, setGroupedDocs] = useState<GroupedDocument[]>([]);
  const [expandedDocs, setExpandedDocs] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pdfViewUrl, setPdfViewUrl] = useState<string | null>(null);

  const fetchGroupedCertificates = useCallback(() => {
    setLoading(true);
    setError(null);
    getCertificatesGrouped()
      .then(setGroupedDocs)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load documents"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchGroupedCertificates();
  }, [fetchGroupedCertificates]);

  const toggleDoc = useCallback((documentId: string) => {
    setExpandedDocs((prev) => ({ ...prev, [documentId]: !prev[documentId] }));
  }, []);

  const viewDocument = useCallback(async (doc: GroupedDocument) => {
    if (doc.certificates.length === 0) return;
    try {
      const { url } = await getCertificateViewUrl(doc.certificates[0].id);
      setPdfViewUrl(url);
    } catch {
      setError("Failed to open document");
    }
  }, []);

  const downloadDocument = useCallback(async (doc: GroupedDocument) => {
    if (doc.certificates.length === 0) return;
    try {
      const { url } = await getCertificateDownloadUrl(doc.certificates[0].id);
      window.open(url, "_blank", "noopener,noreferrer");
    } catch {
      setError("Failed to download document");
    }
  }, []);

  const deleteDocumentHandler = useCallback(
    async (doc: GroupedDocument) => {
      if (!confirm(`Delete "${doc.document_name || "this document"}" and all its certificates? This cannot be undone.`))
        return;
      setError(null);
      try {
        await deleteDocument(doc.document_id);
        fetchGroupedCertificates();
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to delete document");
      }
    },
    [fetchGroupedCertificates]
  );

  const isExpanded = (documentId: string) => expandedDocs[documentId] === true;

  return (
    <div className="space-y-4">
      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
          {error}
        </div>
      )}
      {loading ? (
        <div className="py-8 text-center text-sm text-slate-500">Loading documents…</div>
      ) : groupedDocs.length === 0 ? (
        <div className="py-8 text-center text-sm text-slate-500">
          No documents yet. Upload a multi-certificate PDF from the Upload page.
        </div>
      ) : (
        <div className="space-y-3">
          {groupedDocs.map((doc) => (
            <div
              key={doc.document_id}
              className="rounded-lg border border-slate-200 bg-white p-4 transition-shadow hover:shadow-sm"
            >
              <div
                className="flex cursor-pointer justify-between items-center"
                onClick={() => toggleDoc(doc.document_id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    toggleDoc(doc.document_id);
                  }
                }}
                role="button"
                tabIndex={0}
                aria-expanded={isExpanded(doc.document_id)}
              >
                <div>
                  <div className="font-semibold text-base text-slate-900">
                    {doc.document_name || "Compliance Document"}
                  </div>
                  <div className="mt-0.5 text-sm text-gray-500">
                    {doc.certificates.length} certificate{doc.certificates.length !== 1 ? "s" : ""} • Expires{" "}
                    {getEarliestExpiry(doc.certificates)}
                  </div>
                </div>
                <div className="flex gap-3" onClick={(e) => e.stopPropagation()}>
                  <button
                    type="button"
                    onClick={() => viewDocument(doc)}
                    className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
                  >
                    View
                  </button>
                  <button
                    type="button"
                    onClick={() => downloadDocument(doc)}
                    className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
                  >
                    Download
                  </button>
                  <button
                    type="button"
                    onClick={() => deleteDocumentHandler(doc)}
                    className="rounded border border-red-200 bg-red-50 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-100"
                  >
                    Delete
                  </button>
                </div>
              </div>
              {isExpanded(doc.document_id) && (
                <div className="mt-3 border-t border-slate-200 pt-3">
                  {doc.certificates.map((cert) => (
                    <div
                      key={cert.id}
                      className="flex justify-between py-2 text-sm"
                    >
                      <div className="text-slate-700">
                        {cert.report_number || cert.certificate_name || "—"}
                      </div>
                      <div className="text-slate-500">
                        Expires {formatDate(cert.expiry_date)}
                      </div>
                    </div>
                  ))}
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
