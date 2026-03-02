"use client";

import type { CertificateItem } from "@/lib/api";
import { getCertificateDownloadUrl, getCertificateViewUrl } from "@/lib/api";
import { formatDate } from "@/lib/utils";

interface CertificateCardProps {
  certificate: CertificateItem;
  onView: (url: string) => void;
}

export function CertificateCard({ certificate, onView }: CertificateCardProps) {
  const handleView = async () => {
    if (certificate.view_url) {
      onView(certificate.view_url);
      return;
    }
    try {
      const { url } = await getCertificateViewUrl(certificate.id);
      onView(url);
    } catch {
      // show error in UI if needed
    }
  };

  const handleDownload = async () => {
    let url = certificate.download_url;
    if (!url) {
      try {
        const res = await getCertificateDownloadUrl(certificate.id);
        url = res.url;
      } catch {
        return;
      }
    }
    if (url) {
      window.open(url, "_blank", "noopener,noreferrer");
    }
  };

  const statusClass =
    certificate.status === "Expired"
      ? "bg-red-100 text-red-800"
      : certificate.status === "Expiring Soon"
        ? "bg-amber-100 text-amber-800"
        : "bg-emerald-100 text-emerald-800";

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:shadow-md">
      <div className="mb-3 flex items-start justify-between gap-2">
        <h3 className="font-semibold text-slate-900">
          {certificate.certificate_name || certificate.report_number || "Certificate"}
        </h3>
        <span
          className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${statusClass}`}
        >
          {certificate.status}
        </span>
      </div>
      <dl className="space-y-1 text-sm text-slate-600">
        {certificate.report_number && (
          <div>
            <span className="font-medium text-slate-500">Report No.:</span>{" "}
            {certificate.report_number}
          </div>
        )}
        <div>
          <span className="font-medium text-slate-500">Issue date:</span>{" "}
          {formatDate(certificate.issue_date)}
        </div>
        <div>
          <span className="font-medium text-slate-500">Expiry date:</span>{" "}
          {formatDate(certificate.expiry_date)}
        </div>
      </dl>
      <div className="mt-4 flex gap-2">
        <button
          type="button"
          onClick={handleView}
          className="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          View
        </button>
        <button
          type="button"
          onClick={handleDownload}
          className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          Download
        </button>
      </div>
    </div>
  );
}
