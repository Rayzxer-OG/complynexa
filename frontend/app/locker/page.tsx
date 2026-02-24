"use client";

import { useCallback, useEffect, useState } from "react";
import { getToken } from "@/lib/auth";
import {
  getDocumentDownloadUrl,
  getDocumentViewUrl,
  getDocuments,
  uploadLockerDocument,
  type Document,
} from "@/lib/api";

export default function LockerPage() {
  const [mounted, setMounted] = useState(false);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewUrl, setViewUrl] = useState<string | null>(null);

  const fetchDocuments = useCallback(() => {
    setLoading(true);
    getDocuments()
      .then(setDocuments)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load documents"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted || typeof window === "undefined") return;
    const token = getToken();
    if (!token) {
      window.location.href = "/login";
      return;
    }
    fetchDocuments();
  }, [mounted, fetchDocuments]);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !file.name.toLowerCase().endsWith(".pdf")) {
      setError("Please select a PDF file.");
      return;
    }
    setError(null);
    setUploading(true);
    try {
      await uploadLockerDocument(file);
      fetchDocuments();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleView = async (id: string) => {
    if (!documents.find((d) => d.id === id)?.s3_url) {
      setError("Document has no view URL.");
      return;
    }
    try {
      const { url } = await getDocumentViewUrl(id);
      setViewUrl(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to get view URL");
    }
  };

  const handleDownload = async (id: string) => {
    try {
      const { url } = await getDocumentDownloadUrl(id);
      window.open(url, "_blank", "noopener,noreferrer");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to get download URL");
    }
  };

  if (!mounted) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-slate-500">
        Loading…
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-8 py-6">
      <div className="space-y-8">
        <h1 className="text-2xl font-semibold text-slate-900">Document Locker</h1>
      <p className="text-sm text-slate-600">
        Store PDFs for later. No processing—upload and retrieve only.
      </p>

      <section className="rounded-xl border border-slate-200 bg-slate-50/50 p-6">
        <h2 className="mb-3 text-lg font-medium text-slate-900">Upload file</h2>
        <label className="inline-block cursor-pointer rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
          <input
            type="file"
            accept=".pdf"
            className="sr-only"
            onChange={handleFileSelect}
            disabled={uploading}
          />
          {uploading ? "Uploading…" : "Choose PDF"}
        </label>
      </section>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      <section>
        <h2 className="mb-3 text-lg font-medium text-slate-900">Stored files</h2>
        {loading ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : documents.length === 0 ? (
          <p className="text-sm text-slate-500">No documents yet. Upload a PDF above.</p>
        ) : (
          <div className="overflow-hidden rounded-lg border border-slate-200">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-slate-700">
                    Filename
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-slate-700">
                    Upload date
                  </th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-slate-700">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {documents.map((doc) => (
                  <tr key={doc.id}>
                    <td className="px-4 py-3 text-sm text-slate-900">{doc.filename}</td>
                    <td className="px-4 py-3 text-sm text-slate-600">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {doc.s3_url ? (
                        <span className="flex justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => handleView(doc.id)}
                            className="text-sm font-medium text-blue-600 hover:underline"
                          >
                            View
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDownload(doc.id)}
                            className="text-sm font-medium text-blue-600 hover:underline"
                          >
                            Download
                          </button>
                        </span>
                      ) : (
                        <span className="text-sm text-slate-400">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

        {viewUrl && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
            onClick={() => setViewUrl(null)}
            role="dialog"
            aria-modal="true"
          >
            <div
              className="flex h-full max-h-[90vh] w-full max-w-4xl flex-col rounded-lg bg-white shadow-xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between border-b border-slate-200 px-4 py-2">
                <span className="text-sm font-medium text-slate-700">Document</span>
                <button
                  type="button"
                  onClick={() => setViewUrl(null)}
                  className="rounded p-1 text-slate-500 hover:bg-slate-100"
                >
                  ✕
                </button>
              </div>
              <div className="min-h-0 flex-1 overflow-hidden">
                <iframe src={viewUrl} title="Document PDF" className="h-full w-full border-0" />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
