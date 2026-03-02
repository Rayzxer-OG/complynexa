"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

export function SuccessStep({ unitId }: { unitId: string | null }) {
  const router = useRouter();

  useEffect(() => {
    const path = unitId
      ? `/compliance-checklist?unitId=${encodeURIComponent(unitId)}`
      : "/compliance-checklist";
    router.replace(path);
    router.refresh();
  }, [router, unitId]);

  const handleGoToChecklist = () => {
    const path = unitId
      ? `/compliance-checklist?unitId=${encodeURIComponent(unitId)}`
      : "/compliance-checklist";
    router.replace(path);
    router.refresh();
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-xl font-semibold text-slate-900">You’re all set</h2>
        <p className="mt-2 text-sm text-slate-600">
          Your organization and admin account have been created. Go to the compliance checklist to upload required documents.
        </p>
      </div>

      <div className="flex flex-col gap-2">
        <button
          type="button"
          onClick={handleGoToChecklist}
          className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50"
        >
          Go to Compliance Checklist
        </button>
      </div>
    </div>
  );
}
