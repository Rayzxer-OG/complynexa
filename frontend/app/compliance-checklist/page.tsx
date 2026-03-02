"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ComplianceActivationStepper } from "@/components/compliance/ComplianceActivationStepper";
import { ComplianceChecklistTable } from "@/components/compliance/ComplianceChecklistTable";
import { ConditionalQuestionsCard } from "@/components/compliance/ConditionalQuestionsCard";
import { EditUnitModal } from "@/components/compliance/EditUnitModal";
import { Toast, type ToastVariant } from "@/components/Toast";
import { useComplianceChecklist } from "@/hooks/useComplianceChecklist";
import { getToken, getUnitId, setUnitId as setStoredUnitId } from "@/lib/auth";
import {
  getUnit,
  getConditionalQuestions,
  isProfileSetupRequiredError,
  saveComplianceProfile,
  type UnitInfo,
  type ConditionalQuestion,
} from "@/lib/api";

function ComplianceProgress({
  total,
  uploaded,
  remaining,
}: {
  total: number;
  uploaded: number;
  remaining: number;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/50 px-4 py-3">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-sm">
        <span className="font-medium text-slate-700">
          Total required: <span className="text-slate-900">{total}</span>
        </span>
        <span className="text-slate-600">
          Uploaded: <span className="font-medium text-emerald-700">{uploaded}</span>
        </span>
        <span className="text-slate-600">
          Remaining: <span className="font-medium text-amber-700">{remaining}</span>
        </span>
      </div>
    </div>
  );
}

export default function ComplianceChecklistRoutePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [allowed, setAllowed] = useState(false);
  const [unitId, setUnitId] = useState<string | null>(null);
  const [unitInfo, setUnitInfo] = useState<UnitInfo | null>(null);
  const [unitLoading, setUnitLoading] = useState(true);
  const [unitNotFound, setUnitNotFound] = useState(false);

  const profileCompleted = !!unitInfo?.compliance_profile_completed;
  const confirmedUnitId = unitInfo ? unitId : null;
  const { items, loading, error, refresh } = useComplianceChecklist(confirmedUnitId);
  const [conditionalQuestions, setConditionalQuestions] = useState<ConditionalQuestion[]>([]);
  const [conditionalLoading, setConditionalLoading] = useState(false);
  const [conditionalLoaded, setConditionalLoaded] = useState(false);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [editUnitModalOpen, setEditUnitModalOpen] = useState(false);
  const [toast, setToast] = useState<{ open: boolean; message: string; variant: ToastVariant }>({
    open: false,
    message: "",
    variant: "success",
  });

  const loadConditionalQuestions = useCallback(() => {
    if (unitId === undefined || unitId === null || unitId === "") {
      setConditionalQuestions([]);
      setConditionalLoaded(false);
      return;
    }
    setConditionalLoading(true);
    setConditionalLoaded(false);
    getConditionalQuestions(unitId)
      .then((data) => setConditionalQuestions(Array.isArray(data) ? data : []))
      .catch(() => setConditionalQuestions([]))
      .finally(() => {
        setConditionalLoading(false);
        setConditionalLoaded(true);
      });
  }, [unitId]);

  useEffect(() => {
    loadConditionalQuestions();
  }, [loadConditionalQuestions]);

  const handleConditionalAnswerSaved = useCallback(() => {
    loadConditionalQuestions();
    refresh();
  }, [loadConditionalQuestions, refresh]);

  const handleUnitUpdated = useCallback(() => {
    refresh();
    loadConditionalQuestions();
    if (unitId) getUnit(unitId).then(setUnitInfo).catch(() => {});
  }, [refresh, loadConditionalQuestions, unitId]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    setAllowed(true);
    const fromUrl = searchParams.get("unitId");
    if (fromUrl && fromUrl.trim() !== "") {
      setUnitId(fromUrl.trim());
      setStoredUnitId(fromUrl.trim());
    } else {
      setUnitId(getUnitId());
    }
  }, [router, searchParams]);

  useEffect(() => {
    if (!unitId) {
      setUnitInfo(null);
      setUnitNotFound(false);
      setUnitLoading(false);
      return;
    }
    let cancelled = false;
    setUnitLoading(true);
    setUnitNotFound(false);
    getUnit(unitId)
      .then((data) => {
        if (cancelled) return;
        console.log("Industry ID:", data.industry);
        setUnitInfo(data);
        setUnitNotFound(false);
      })
      .catch((e) => {
        if (!cancelled && isProfileSetupRequiredError(e)) {
          setUnitInfo(null);
        } else if (!cancelled) {
          setUnitInfo(null);
          setUnitNotFound(e instanceof Error && e.message === "Unit not found");
        }
      })
      .finally(() => {
        if (!cancelled) setUnitLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [unitId, router]);

  const handleProfileSaveAndShowChecklist = useCallback(async () => {
    if (unitId == null || unitId === "") {
      setProfileError("No unit selected. Please refresh or return to the dashboard.");
      return;
    }
    console.log("Saving checklist for unitId:", unitId);
    setProfileError(null);
    setProfileSaving(true);
    try {
      await saveComplianceProfile(unitId, []);
      const data = await getUnit(unitId);
      setUnitInfo(data);
      setToast({ open: true, message: "Compliance profile saved. Loading checklist…", variant: "success" });
    } catch (e) {
      setProfileError(e instanceof Error ? e.message : "Failed to save");
    } finally {
      setProfileSaving(false);
    }
  }, [unitId]);

  if (!allowed) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-slate-500">
        Loading…
      </div>
    );
  }

  if (unitLoading) {
    return (
      <div className="mx-auto max-w-7xl px-6 py-6 lg:px-8">
        <div className="space-y-6">
          <div className="h-8 w-48 animate-pulse rounded bg-slate-200" />
          <div className="rounded-xl border border-slate-200 bg-white py-12">
            <div className="flex flex-col items-center justify-center gap-3 text-slate-500">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
              <p className="text-sm">Loading unit…</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const unitExists = !!unitInfo;
  const uploadedCount = items.filter(
    (i) =>
      i.status === "valid" ||
      i.status === "uploaded" ||
      i.status === "expiring_soon"
  ).length;
  const remainingCount = items.length - uploadedCount;
  const checklistLoaded = !loading && items.length >= 0;

  return (
    <div className="mx-auto max-w-7xl px-6 py-6 lg:px-8">
      <div className="space-y-6">
        {unitInfo && (
          <div className="rounded-xl border border-slate-200 bg-slate-800 px-4 py-4 text-white shadow-sm flex flex-wrap items-start justify-between gap-2">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                Unit
              </p>
              <p className="mt-1 text-lg font-semibold text-white">{unitInfo.unit_name}</p>
              <p className="mt-0.5 text-sm text-slate-200">{unitInfo.address}</p>
            </div>
            <div className="flex gap-2">
              {unitId && (
                <>
                  <Link
                    href="/unit-settings"
                    className="rounded-md border border-slate-500 bg-transparent px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700"
                  >
                    Unit Settings
                  </Link>
                  <button
                    type="button"
                    onClick={() => setEditUnitModalOpen(true)}
                    className="rounded-md border border-slate-500 bg-transparent px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700"
                  >
                    Edit unit
                  </button>
                </>
              )}
            </div>
          </div>
        )}
        {unitId && (
          <EditUnitModal
            unitId={unitId}
            unit={unitInfo}
            open={editUnitModalOpen}
            onClose={() => setEditUnitModalOpen(false)}
            onSuccess={handleUnitUpdated}
          />
        )}
          <div className="flex items-center justify-between">
          <div>
            <Link
              href="/dashboard"
              className="text-sm font-medium text-slate-600 hover:text-slate-900"
            >
              ← Dashboard
            </Link>
            <h1 className="mt-1 text-2xl font-semibold text-slate-900">
              Compliance Checklist
            </h1>
            <p className="mt-0.5 text-sm text-slate-500">
              Required compliance documents for your unit. Upload documents to satisfy each requirement. Mandatory, optional, and conditional (where applicable) rows are from the checklist.
            </p>
          </div>
        </div>

        {unitId && unitInfo && (
          <div className="mt-4">
            <ComplianceActivationStepper unitId={unitId} refreshDeps={items.length} />
          </div>
        )}

        {!unitId ? (
          <div className="rounded-xl border border-slate-200 bg-slate-50/50 py-12 px-6 text-center">
            <p className="font-medium text-slate-700">No unit found</p>
            <p className="mt-1 text-sm text-slate-500">
              Complete onboarding to create your unit and see compliance requirements.
            </p>
            <Link
              href="/dashboard"
              className="mt-4 inline-block rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Back to Dashboard
            </Link>
          </div>
        ) : !unitExists ? (
          unitNotFound ? (
            <div className="rounded-xl border border-slate-200 bg-slate-50/50 py-12 px-6 text-center">
              <p className="font-medium text-slate-700">Unit not found</p>
              <p className="mt-1 text-sm text-slate-500">
                The selected unit could not be loaded. It may have been removed or you may not have access.
              </p>
              <Link
                href="/dashboard"
                className="mt-4 inline-block rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Back to Dashboard
              </Link>
            </div>
          ) : (
            <div className="rounded-xl border border-amber-200 bg-amber-50/50 py-12 px-6 text-center">
              <p className="font-medium text-amber-800">Could not load unit</p>
              <p className="mt-1 text-sm text-amber-700">
                Something went wrong. Please try again or go back to the dashboard.
              </p>
              <Link
                href="/dashboard"
                className="mt-4 inline-block rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Back to Dashboard
              </Link>
            </div>
          )
        ) : unitInfo && (unitInfo.industry == null || unitInfo.industry === "") ? (
          <div className="rounded-xl border border-red-200 bg-red-50/50 py-12 px-6 text-center">
            <p className="font-medium text-red-800">Industry not linked to unit</p>
            <p className="mt-1 text-sm text-red-700">
              This unit has no industry set. Use <strong>Edit unit</strong> above to select your industry (e.g. Pharmaceutical) so we can show the right compliance questions and checklist.
            </p>
            <Link
              href="/dashboard"
              className="mt-4 inline-block rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Back to Dashboard
            </Link>
          </div>
        ) : (
          <>
            {/* UNIT ATTRIBUTES: only for updating attributes; shown above checklist when conditional questions exist */}
            {unitId && conditionalLoaded && conditionalQuestions.length > 0 && (
              <>
                {profileError && (
                  <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-md" role="alert">
                    {profileError}
                  </p>
                )}
                <ConditionalQuestionsCard
                  unitId={unitId}
                  questions={conditionalQuestions}
                  onAnswerSaved={() => {
                    loadConditionalQuestions();
                    if (unitId) getUnit(unitId).then(setUnitInfo).catch(() => {});
                    refresh();
                  }}
                />
              </>
            )}
            {unitId && conditionalLoaded && conditionalQuestions.length === 0 && !profileCompleted && (
              <div className="rounded-xl border border-amber-200 bg-amber-50/50 px-4 py-4 space-y-3">
                <p className="text-sm text-slate-600">
                  No conditional questions for this unit. Save to load your checklist.
                </p>
                {profileError && (
                  <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-md" role="alert">
                    {profileError}
                  </p>
                )}
                <button
                  type="button"
                  onClick={handleProfileSaveAndShowChecklist}
                  disabled={profileSaving}
                  className="rounded-xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50"
                >
                  {profileSaving ? "Saving…" : "Save and show checklist"}
                </button>
              </div>
            )}

            {/* Checklist: always rendered from checklist API (mandatory, optional, conditional where applies=True) */}
            <div id="compliance-checklist-section" className="scroll-mt-4">
              {loading ? (
                <div className="rounded-xl border border-slate-200 bg-white py-12">
                  <div className="flex flex-col items-center justify-center gap-3 py-8 text-slate-500">
                    <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
                    <p className="text-sm">Loading checklist…</p>
                  </div>
                </div>
              ) : error ? (
                <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {typeof error === "string" ? error : (error as { message?: string })?.message ?? "Failed to load checklist"}
                </div>
              ) : (
                <>
                  {checklistLoaded && items.length > 0 && (
                    <>
                      <div className="rounded-xl border border-slate-200 bg-white px-4 py-4 shadow-sm">
                        <p className="text-sm font-medium text-slate-900">
                          Welcome to Complynexa. Upload your compliance documents to activate automated monitoring and reminders.
                        </p>
                      </div>
                      <ComplianceProgress
                        total={items.length}
                        uploaded={uploadedCount}
                        remaining={remainingCount}
                      />
                    </>
                  )}
                  {items.length === 0 ? (
                    <div className="rounded-xl border border-slate-200 bg-white py-12 px-6 text-center">
                      <p className="font-medium text-slate-700">No compliance requirements found</p>
                      <p className="mt-1 text-sm text-slate-500">
                        Your unit has no applicable requirements, or complete the unit attributes above and save to generate them.
                      </p>
                    </div>
                  ) : (
                    <ComplianceChecklistTable
                      items={items}
                      unitId={unitId!}
                      onUploadSuccess={refresh}
                    />
                  )}
                </>
              )}
            </div>
          </>
        )}
      </div>
      <Toast
        open={toast.open}
        message={toast.message}
        variant={toast.variant}
        onClose={() => setToast((p) => ({ ...p, open: false }))}
      />
    </div>
  );
}
