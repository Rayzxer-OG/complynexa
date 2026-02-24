"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { setToken } from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const registerRes = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, full_name: fullName }),
      });
      const registerData = await registerRes.json().catch(() => ({}));
      if (!registerRes.ok) {
        const detail = typeof registerData.detail === "string"
          ? registerData.detail
          : Array.isArray(registerData.detail)
            ? registerData.detail.map((x: { msg?: string }) => x?.msg).filter(Boolean).join(". ")
            : registerData.message ?? "Registration failed";
        setError(detail || `Registration failed (${registerRes.status})`);
        return;
      }
      const loginRes = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const loginData = await loginRes.json().catch(() => ({}));
      if (loginRes.ok && loginData.access_token) {
        setToken(loginData.access_token);
        router.push("/dashboard");
        router.refresh();
      } else {
        router.push("/login");
      }
    } catch {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-sm space-y-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <h1 className="text-xl font-semibold text-slate-900">Register</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="fullName" className="mb-1 block text-sm font-medium text-slate-700">
            Full name
          </label>
          <input
            id="fullName"
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="email" className="mb-1 block text-sm font-medium text-slate-700">
            Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label htmlFor="password" className="mb-1 block text-sm font-medium text-slate-700">
            Password (min 8 characters)
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        {error && (
          <p className="text-sm text-red-600" role="alert">
            {error}
          </p>
        )}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          {loading ? "Creating account…" : "Register"}
        </button>
      </form>
      <p className="text-center text-sm text-slate-500">
        Already have an account?{" "}
        <a href="/login" className="font-medium text-slate-800 hover:underline">
          Log in
        </a>
      </p>
    </div>
  );
}
