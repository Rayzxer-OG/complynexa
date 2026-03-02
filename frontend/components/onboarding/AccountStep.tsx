"use client";

import { useState } from "react";
import { setOrganizationId, setToken, setUnitId } from "@/lib/auth";
import { submitOnboarding, type OnboardingBody, type OnboardingOrganization, type OnboardingResponse } from "@/lib/api";

export interface AccountStepData {
  full_name: string;
  email: string;
  mobile: string;
  password: string;
  alternate_email: string;
  alternate_mobile: string;
}

interface AccountStepProps {
  data: AccountStepData;
  onChange: (data: AccountStepData) => void;
  organizationPayload: OnboardingOrganization;
  submitButtonLabel?: string;
  onSuccess: (result: OnboardingResponse) => void;
}

export function AccountStep({
  data,
  onChange,
  organizationPayload,
  submitButtonLabel = "Complete Registration",
  onSuccess,
}: AccountStepProps) {
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const set = (partial: Partial<AccountStepData>) =>
    onChange({ ...data, ...partial });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const body: OnboardingBody = {
        organization: organizationPayload,
        user: {
          full_name: data.full_name.trim(),
          email: data.email.trim(),
          password: data.password,
          mobile: data.mobile.trim(),
          alternate_email: data.alternate_email?.trim() || undefined,
          alternate_mobile: data.alternate_mobile?.trim() || undefined,
        },
      };
      const result = await submitOnboarding(body);
      setToken(result.access_token);
      if (result.organization_id) setOrganizationId(result.organization_id);
      if (result.unit_id != null && result.unit_id !== "") {
        setUnitId(result.unit_id);
      }
      onSuccess(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  const requiredValid =
    data.full_name?.trim() &&
    data.email?.trim() &&
    data.mobile?.trim() &&
    data.password &&
    data.password.length >= 8;

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="fullName" className="mb-1 block text-sm font-medium text-slate-700">
          Full Name <span className="text-red-500">*</span>
        </label>
        <input
          id="fullName"
          type="text"
          value={data.full_name}
          onChange={(e) => set({ full_name: e.target.value })}
          required
          className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        />
      </div>
      <div>
        <label htmlFor="email" className="mb-1 block text-sm font-medium text-slate-700">
          Email <span className="text-red-500">*</span>
        </label>
        <input
          id="email"
          type="email"
          value={data.email}
          onChange={(e) => set({ email: e.target.value })}
          required
          className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        />
      </div>
      <div>
        <label htmlFor="mobile" className="mb-1 block text-sm font-medium text-slate-700">
          Mobile Number <span className="text-red-500">*</span>
        </label>
        <input
          id="mobile"
          type="tel"
          value={data.mobile}
          onChange={(e) => set({ mobile: e.target.value })}
          required
          className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        />
      </div>
      <div>
        <label htmlFor="password" className="mb-1 block text-sm font-medium text-slate-700">
          Password <span className="text-red-500">*</span>
        </label>
        <input
          id="password"
          type="password"
          value={data.password}
          onChange={(e) => set({ password: e.target.value })}
          required
          minLength={8}
          className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        />
        <p className="mt-0.5 text-xs text-slate-500">Minimum 8 characters</p>
      </div>
      <div>
        <label htmlFor="altEmail" className="mb-1 block text-sm font-medium text-slate-600">
          Alternate Email
        </label>
        <input
          id="altEmail"
          type="email"
          value={data.alternate_email}
          onChange={(e) => set({ alternate_email: e.target.value })}
          className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        />
      </div>
      <div>
        <label htmlFor="altMobile" className="mb-1 block text-sm font-medium text-slate-600">
          Alternate Mobile
        </label>
        <input
          id="altMobile"
          type="tel"
          value={data.alternate_mobile}
          onChange={(e) => set({ alternate_mobile: e.target.value })}
          className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        />
      </div>
      {error && (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
      <button
        type="submit"
        disabled={loading || !requiredValid}
        className="w-full rounded-xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white shadow-md hover:bg-slate-800 disabled:opacity-50"
      >
        {loading ? "Creating account…" : submitButtonLabel}
      </button>
    </form>
  );
}
