"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { Document } from "@/lib/api";
import { deleteDocument } from "@/lib/api";
import { formatDate, getStatus, type DocumentStatus } from "@/lib/utils";

function TrashIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M3 6h18" />
      <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
      <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
      <line x1="10" y1="11" x2="10" y2="17" />
      <line x1="14" y1="11" x2="14" y2="17" />
    </svg>
  );
}

const statusConfig: Record<
  DocumentStatus,
  { label: string; className: string }
> = {
  expired: { label: "Expired", className: "bg-red-100 text-red-800" },
  expiring_soon: {
    label: "Expiring Soon",
    className: "bg-amber-100 text-amber-800",
  },
  active: { label: "Active", className: "bg-emerald-100 text-emerald-800" },
};

interface DocumentTableProps {
  documents: Document[];
  onDeleted?: () => void;
}

export function DocumentTable({ documents, onDeleted }: DocumentTableProps) {
  const router = useRouter();
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async (doc: Document) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this document?"
    );
    if (!confirmed) return;
    setError(null);
    setDeletingId(doc.id);
    try {
      await deleteDocument(doc.id);
      onDeleted?.();
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setDeletingId(null);
    }
  };

  const renderStatus = (expiryDate: string | null) => {
    const status = getStatus(expiryDate);
    if (status === null) return <span className="text-slate-500">—</span>;
    const { label, className } = statusConfig[status];
    return (
      <span
        className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${className}`}
      >
        {label}
      </span>
    );
  };

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      {error && (
        <div className="border-b border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
          {error}
        </div>
      )}
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-50">
          <tr>
            <th
              scope="col"
              className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600"
            >
              Document Name
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600"
            >
              Category
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600"
            >
              Expiry Date
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600"
            >
              Status
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-slate-600"
            >
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200 bg-white">
          {documents.length === 0 ? (
            <tr>
              <td
                colSpan={5}
                className="px-4 py-8 text-center text-sm text-slate-500"
              >
                No documents yet. Upload one from the Upload page.
              </td>
            </tr>
          ) : (
            documents.map((doc) => (
              <tr key={doc.id} className="hover:bg-slate-50">
                <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-slate-900">
                  {doc.document_name || doc.filename}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-600">
                  {doc.category ?? "—"}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-600">
                  {formatDate(doc.expiry_date)}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm">
                  {renderStatus(doc.expiry_date)}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-right">
                  <button
                    type="button"
                    onClick={() => handleDelete(doc)}
                    disabled={deletingId === doc.id}
                    className="inline-flex items-center justify-center rounded-md p-1.5 text-red-600 hover:bg-red-50 hover:text-red-700 disabled:opacity-50"
                    title="Delete document"
                    aria-label={`Delete ${doc.document_name || doc.filename}`}
                  >
                    <TrashIcon />
                    {deletingId === doc.id && (
                      <span className="ml-1 text-xs">…</span>
                    )}
                  </button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
