"use client";

import {
  getComplianceDocument,
  getDocumentViewUrl,
  type ComplianceChecklistItem,
} from "@/lib/api";
import { formatDateDDMMYYYY } from "@/lib/utils";
import { UploadComplianceModal } from "./UploadComplianceModal";
import { useState } from "react";

function ApplicabilityBadge({ flag }: { flag: string | null | undefined }) {
  if (!flag) return null;
  const f = flag.toUpperCase();
  const style =
    f === "M"
      ? "bg-red-100 text-red-800"
      : f === "C"
        ? "bg-amber-100 text-amber-800"
        : "bg-slate-100 text-slate-700";
  const label =
    f === "M" ? "Mandatory" : f === "C" ? "Conditional" : f === "O" ? "Optional" : flag;
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${style}`}
    >
      {label}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const style =
    status === "expired"
      ? "bg-red-100 text-red-800"
      : status === "expiring_soon"
        ? "bg-amber-100 text-amber-800"
        : status === "valid" || status === "uploaded"
          ? "bg-emerald-100 text-emerald-800"
          : "bg-slate-100 text-slate-700";
  const label =
    status === "expiring_soon"
      ? "Expiring soon"
      : status === "pending"
        ? "Pending"
        : status.charAt(0).toUpperCase() + status.slice(1);
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${style}`}
    >
      {label}
    </span>
  );
}

interface ComplianceChecklistTableProps {
  items: ComplianceChecklistItem[];
  unitId: string;
  onUploadSuccess: () => void;
}

export function ComplianceChecklistTable({
  items,
  unitId,
  onUploadSuccess,
}: ComplianceChecklistTableProps) {
  const [uploadModal, setUploadModal] = useState<{
    open: boolean;
    name: string;
    complianceRequirementId: string;
    unitId: string;
  }>({ open: false, name: "", complianceRequirementId: "", unitId: "" });
  const [viewError, setViewError] = useState<string | null>(null);
  const [viewLoadingId, setViewLoadingId] = useState<string | null>(null);

  const openUpload = (row: ComplianceChecklistItem) => {
    setUploadModal({
      open: true,
      name: row.compliance_name,
      complianceRequirementId: row.compliance_requirement_id,
      unitId,
    });
  };

  return (
    <>
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Compliance name
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Applicability flag
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600">
                  License number
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Issuing authority
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Issue date
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Expiry date
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Description
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Status
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Action
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {items.map((row) => {
                const hasDocument = row.status !== "pending";
                return (
                <tr key={row.compliance_requirement_id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 text-sm font-medium text-slate-900">
                    <div>{row.compliance_name}</div>
                    {row.required_because && (
                      <div className="mt-1 text-xs font-normal text-slate-500">
                        Required because: {row.required_because.condition_question} = {row.required_because.user_response}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <ApplicabilityBadge flag={row.applicability_flag} />
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-700">
                    {row.license_number ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-700 max-w-[180px]">
                    {row.issuing_authority ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-700 whitespace-nowrap">
                    {row.issue_date ? formatDateDDMMYYYY(row.issue_date) : "—"}
                  </td>
                  <td className="px-4 py-3 text-sm whitespace-nowrap">
                    {row.expiry_date ? (
                      row.status === "expired" ? (
                        <span className="text-red-700 font-medium">{formatDateDDMMYYYY(row.expiry_date)}</span>
                      ) : row.status === "expiring_soon" ? (
                        <span className="text-amber-700 font-medium">{formatDateDDMMYYYY(row.expiry_date)}</span>
                      ) : (
                        <span className="text-slate-700">{formatDateDDMMYYYY(row.expiry_date)}</span>
                      )
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-600 max-w-[200px]">
                    {row.description ?? "—"}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={row.status} />
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right">
                    {(row.status === "pending" || row.status === "expired") && (
                      <button
                        type="button"
                        onClick={() => openUpload(row)}
                        className={`rounded-md px-3 py-1.5 text-sm font-medium ${
                          row.status === "expired"
                            ? "border border-amber-300 bg-amber-50 text-amber-800 hover:bg-amber-100"
                            : "bg-slate-800 text-white hover:bg-slate-700"
                        }`}
                      >
                        {row.status === "expired" ? "Renew" : "Upload"}
                      </button>
                    )}
                    {(row.status === "valid" ||
                      row.status === "uploaded" ||
                      row.status === "expiring_soon") && (
                      <button
                        type="button"
                        disabled={viewLoadingId === row.compliance_requirement_id}
                        onClick={async () => {
                          setViewError(null);
                          setViewLoadingId(row.compliance_requirement_id);
                          try {
                            const doc = await getComplianceDocument(
                              row.compliance_requirement_id
                            );
                            const { url } = await getDocumentViewUrl(doc.id);
                            window.open(url, "_blank");
                          } catch {
                            setViewError("Document not found");
                          } finally {
                            setViewLoadingId(null);
                          }
                        }}
                        className="inline-block rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                      >
                        {viewLoadingId === row.compliance_requirement_id
                          ? "Opening…"
                          : "View"}
                      </button>
                    )}
                  </td>
                </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {viewError && (
        <div className="mt-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800">
          {viewError}
        </div>
      )}

      <UploadComplianceModal
        open={uploadModal.open}
        onClose={() =>
          setUploadModal((p) => ({ ...p, open: false }))
        }
        complianceName={uploadModal.name}
        complianceRequirementId={uploadModal.complianceRequirementId}
        unitId={uploadModal.unitId}
        onSuccess={() => {
          onUploadSuccess();
        }}
      />
    </>
  );
}
