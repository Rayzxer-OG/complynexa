"use client";

import { useEffect, useState } from "react";
import { getActivationStatus, type ActivationStatus } from "@/lib/api";

export type StepState = "done" | "in_progress" | "locked";

const STEP_LABELS = {
  registration: "Registration",
  profile: "Compliance Profile Setup",
  monitoring: "Compliance Monitoring Active",
} as const;

function stepState(
  status: ActivationStatus
): Record<"registration" | "profile" | "monitoring", StepState> {
  const profileDone = status.compliance_profile_completed;
  const matrixDone = status.compliance_matrix_generated;
  const monitoringDone = status.monitoring_active;

  return {
    registration: "done",
    profile: profileDone ? "done" : "in_progress",
    monitoring: monitoringDone
      ? "done"
      : !profileDone || !matrixDone
        ? "locked"
        : "in_progress",
  };
}

interface ComplianceActivationStepperProps {
  unitId: string | null;
  /** Optional: refetch after an action (e.g. after saving profile). */
  refreshDeps?: unknown;
}

export function ComplianceActivationStepper({
  unitId,
  refreshDeps,
}: ComplianceActivationStepperProps) {
  const [status, setStatus] = useState<ActivationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!unitId) {
      setStatus(null);
      setLoading(false);
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    getActivationStatus(unitId)
      .then(setStatus)
      .catch((e) => {
        setError(e instanceof Error ? e.message : "Failed to load status");
        setStatus(null);
      })
      .finally(() => setLoading(false));
  }, [unitId, refreshDeps]);

  if (!unitId || loading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-slate-50/50 px-4 py-3">
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
          Loading activation progress…
        </div>
      </div>
    );
  }

  if (error || !status) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50/50 px-4 py-3 text-sm text-amber-800">
        {error ?? "Unable to load activation status"}
      </div>
    );
  }

  const states = stepState(status);

  return (
    <div className="rounded-xl border border-slate-200 bg-white px-4 py-4 shadow-sm">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        {/* Step 1: Registration */}
        <div className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100 text-emerald-700" aria-hidden>
            ✔
          </span>
          <span className="text-sm font-medium text-slate-800">{STEP_LABELS.registration}</span>
        </div>

        <span className="text-slate-300" aria-hidden>→</span>

        {/* Step 2: Compliance Profile Setup */}
        <div className="flex items-center gap-2">
          {states.profile === "done" ? (
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100 text-emerald-700" aria-hidden>
              ✔
            </span>
          ) : states.profile === "in_progress" ? (
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-100 text-amber-700" aria-hidden>
              ⏳
            </span>
          ) : (
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 text-slate-500" aria-hidden>
              ⏳
            </span>
          )}
          <span className="text-sm font-medium text-slate-800">{STEP_LABELS.profile}</span>
        </div>

        <span className="text-slate-300" aria-hidden>→</span>

        {/* Step 3: Compliance Monitoring Active */}
        <div className="flex items-center gap-2">
          {states.monitoring === "done" ? (
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100 text-emerald-700" aria-hidden>
              ✔
            </span>
          ) : states.monitoring === "locked" ? (
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-200 text-slate-500" aria-hidden title="Complete previous steps first">
              🔒
            </span>
          ) : (
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-100 text-amber-700" aria-hidden>
              ⏳
            </span>
          )}
          <span className="text-sm font-medium text-slate-800">{STEP_LABELS.monitoring}</span>
        </div>
      </div>
    </div>
  );
}
