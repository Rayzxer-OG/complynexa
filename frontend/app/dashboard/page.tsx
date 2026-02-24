"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { DashboardWithFilters } from "@/components/DashboardWithFilters";
import { getToken } from "@/lib/auth";

export default function DashboardPage() {
  const router = useRouter();
  const [allowed, setAllowed] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    setAllowed(true);
  }, [router]);

  if (!allowed) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-slate-500">
        Loading…
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-8 py-6">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
          <div className="flex gap-2">
            <Link
              href="/locker"
              className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Document Locker
            </Link>
            <Link
              href="/upload"
              className="rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
            >
              Upload document
            </Link>
          </div>
        </div>
        <DashboardWithFilters />
        <p className="text-xs text-slate-500">
          Certificates are created when you upload a multi-certificate PDF from the Upload page. View and Download open the split certificate PDF.
        </p>
      </div>
    </div>
  );
}
