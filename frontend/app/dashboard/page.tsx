"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ComplianceActivationStepper } from "@/components/compliance/ComplianceActivationStepper";
import { DashboardWithFilters } from "@/components/DashboardWithFilters";
import { useComplianceChecklist } from "@/hooks/useComplianceChecklist";
import { getUnit, isProfileSetupRequiredError, type UnitInfo } from "@/lib/api";
import { getToken, getUnitId } from "@/lib/auth";

export default function DashboardPage() {
  const router = useRouter();
  const [allowed, setAllowed] = useState(false);
  const [unitId, setUnitId] = useState<string | null>(null);
  const [unitInfo, setUnitInfo] = useState<UnitInfo | null>(null);
  const [unitLoading, setUnitLoading] = useState(true);
  const [unitNotFound, setUnitNotFound] = useState(false);

  const confirmedUnitId = unitInfo ? unitId : null;
  const { items: complianceItems, loading: complianceLoading, error: checklistError } =
    useComplianceChecklist(confirmedUnitId);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    setAllowed(true);
    setUnitId(getUnitId());
  }, [router]);

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
      .then((unit) => {
        if (cancelled) return;
        if (unit && unit.compliance_profile_completed === false) {
          router.replace("/compliance-checklist");
          return;
        }
        setUnitInfo(unit ?? null);
        setUnitNotFound(false);
      })
      .catch((e) => {
        if (!cancelled && isProfileSetupRequiredError(e)) router.replace("/compliance-checklist");
        else if (!cancelled) {
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

  useEffect(() => {
    if (checklistError && isProfileSetupRequiredError(checklistError)) {
      router.replace("/compliance-checklist");
    }
  }, [checklistError, router]);

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
          <div className="h-8 w-64 animate-pulse rounded bg-slate-200" />
          <div className="rounded-xl border border-slate-200 bg-white py-12">
            <div className="flex flex-col items-center justify-center gap-3 text-slate-500">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
              <p className="text-sm">Loading…</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const pendingCount = complianceItems.filter(
    (i) => i.status === "pending" || i.status === "expired"
  ).length;

  return (
    <div className="mx-auto max-w-7xl px-6 py-6 lg:px-8">
      <div className="space-y-6">
        {unitId && unitInfo && (
          <ComplianceActivationStepper unitId={unitId} refreshDeps={complianceItems.length} />
        )}
        {unitId && !unitInfo && unitNotFound && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 py-6 px-4 text-center">
            <p className="font-medium text-amber-800">Unit not found</p>
            <p className="mt-1 text-sm text-amber-700">
              The selected unit could not be loaded. You can still use the document locker below.
            </p>
          </div>
        )}
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
          <div className="flex gap-2">
            <Link
              href="/compliance-checklist"
              className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Compliance Checklist
            </Link>
            <Link
              href="/locker"
              className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Document Locker
            </Link>
            <Link
              href="/unit-settings"
              className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Unit Settings
            </Link>
          </div>
        </div>

        {unitId && unitInfo && !complianceLoading && complianceItems.length > 0 && (
          <Link
            href="/compliance-checklist"
            className="block rounded-xl border border-slate-200 bg-white p-4 shadow-sm hover:border-slate-300 hover:bg-slate-50/50"
          >
            <h2 className="text-sm font-semibold text-slate-900">
              Compliance Checklist
            </h2>
            <p className="mt-1 text-sm text-slate-600">
              {complianceItems.length} requirement
              {complianceItems.length !== 1 ? "s" : ""}
              {pendingCount > 0
                ? ` · ${pendingCount} pending upload${pendingCount !== 1 ? "s" : ""}`
                : " · All satisfied"}
            </p>
            <span className="mt-2 inline-block text-sm font-medium text-slate-800">
              View checklist →
            </span>
          </Link>
        )}

        <DashboardWithFilters />
        <p className="text-xs text-slate-500">
          Certificates are created when you upload a multi-certificate PDF from the Upload page. View and Download open the split certificate PDF.
        </p>
      </div>
    </div>
  );
}
