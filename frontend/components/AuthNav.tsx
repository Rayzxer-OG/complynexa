"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { clearToken, getToken } from "@/lib/auth";

export function AuthNav() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const hasToken = mounted && getToken();

  const handleLogout = () => {
    clearToken();
    router.push("/login");
    router.refresh();
  };

  const showLoggedIn = !!hasToken;

  return (
    <nav className="flex items-center gap-6">
      <Link
        href="/dashboard"
        className="text-sm font-medium text-slate-600 hover:text-slate-900"
      >
        Dashboard
      </Link>
      <Link
        href="/upload"
        className="text-sm font-medium text-slate-600 hover:text-slate-900"
      >
        Upload
      </Link>
      <Link
        href="/locker"
        className="text-sm font-medium text-slate-600 hover:text-slate-900"
      >
        Document Locker
      </Link>
      {showLoggedIn ? (
        <button
          type="button"
          onClick={handleLogout}
          className="text-sm font-medium text-slate-600 hover:text-slate-900"
        >
          Log out
        </button>
      ) : (
        <>
          <Link
            href="/login"
            className="text-sm font-medium text-slate-600 hover:text-slate-900"
          >
            Login
          </Link>
          <Link
            href="/register"
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Register
          </Link>
        </>
      )}
    </nav>
  );
}
