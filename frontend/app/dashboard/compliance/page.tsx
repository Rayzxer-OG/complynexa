"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

/** Redirect to canonical Compliance Checklist page. */
export default function DashboardComplianceRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/compliance-checklist");
  }, [router]);
  return (
    <div className="flex min-h-[40vh] items-center justify-center text-slate-500">
      Redirecting to Compliance Checklist…
    </div>
  );
}
