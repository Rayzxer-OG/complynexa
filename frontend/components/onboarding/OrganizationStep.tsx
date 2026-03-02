"use client";

import { useEffect, useState } from "react";
import { getIndustries, type Industry, type OnboardingOrganization } from "@/lib/api";

const STATE_OPTIONS = [
  "Andhra Pradesh",
  "Arunachal Pradesh",
  "Assam",
  "Bihar",
  "Chhattisgarh",
  "Goa",
  "Gujarat",
  "Haryana",
  "Himachal Pradesh",
  "Jharkhand",
  "Karnataka",
  "Kerala",
  "Madhya Pradesh",
  "Maharashtra",
  "Manipur",
  "Meghalaya",
  "Mizoram",
  "Nagaland",
  "Odisha",
  "Punjab",
  "Rajasthan",
  "Sikkim",
  "Tamil Nadu",
  "Telangana",
  "Tripura",
  "Uttar Pradesh",
  "Uttarakhand",
  "West Bengal",
  "Delhi",
  "Other",
];

export interface OrganizationStepData {
  organization_name: string;
  unit_name: string;
  address: string;
  state: string;
  industry_id: string;
}

interface OrganizationStepProps {
  data: OrganizationStepData;
  onChange: (data: OrganizationStepData) => void;
  onNext: () => void;
}

export function OrganizationStep({ data, onChange, onNext }: OrganizationStepProps) {
  const [industries, setIndustries] = useState<Industry[]>([]);
  const [industriesLoading, setIndustriesLoading] = useState(true);
  const [industriesError, setIndustriesError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIndustriesLoading(true);
    setIndustriesError(null);
    getIndustries()
      .then((list) => {
        if (!cancelled) setIndustries(list);
      })
      .catch((e) => {
        if (!cancelled) setIndustriesError(e instanceof Error ? e.message : "Failed to load industries");
      })
      .finally(() => {
        if (!cancelled) setIndustriesLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  const set = (partial: Partial<OrganizationStepData>) =>
    onChange({ ...data, ...partial });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (
      !data.organization_name?.trim() ||
      !data.unit_name?.trim() ||
      !data.address?.trim() ||
      !data.state ||
      !data.industry_id
    ) {
      return;
    }
    onNext();
  };

  const isValid =
    !industriesLoading &&
    industriesError === null &&
    !!data.organization_name?.trim() &&
    !!data.unit_name?.trim() &&
    !!data.address?.trim() &&
    !!data.state &&
    !!data.industry_id;

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="organizationName" className="mb-1 block text-sm font-medium text-slate-700">
          Organization Name <span className="text-red-500">*</span>
        </label>
        <input
          id="organizationName"
          type="text"
          value={data.organization_name}
          onChange={(e) => set({ organization_name: e.target.value })}
          required
          className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        />
      </div>
      <div>
        <label htmlFor="unitName" className="mb-1 block text-sm font-medium text-slate-700">
          Unit / Factory Name <span className="text-red-500">*</span>
        </label>
        <input
          id="unitName"
          type="text"
          value={data.unit_name}
          onChange={(e) => set({ unit_name: e.target.value })}
          required
          className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        />
      </div>
      <div>
        <label htmlFor="address" className="mb-1 block text-sm font-medium text-slate-700">
          Unit Address <span className="text-red-500">*</span>
        </label>
        <input
          id="address"
          type="text"
          value={data.address}
          onChange={(e) => set({ address: e.target.value })}
          required
          className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        />
      </div>
      <div>
        <label htmlFor="state" className="mb-1 block text-sm font-medium text-slate-700">
          State <span className="text-red-500">*</span>
        </label>
        <select
          id="state"
          value={data.state}
          onChange={(e) => set({ state: e.target.value })}
          required
          className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        >
          <option value="">Select</option>
          {STATE_OPTIONS.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="industry" className="mb-1 block text-sm font-medium text-slate-700">
          Industry Sector <span className="text-red-500">*</span>
        </label>
        {industriesLoading ? (
          <div className="w-full rounded-xl border border-slate-300 bg-slate-50 px-3 py-2.5 text-sm text-slate-500">
            Loading industries…
          </div>
        ) : industriesError ? (
          <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700" role="alert">
            {industriesError}
          </div>
        ) : (
          <select
            id="industry"
            value={data.industry_id}
            onChange={(e) => set({ industry_id: e.target.value })}
            required
            className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
            aria-describedby="industry-hint"
          >
            <option value="">Select manufacturing industry</option>
            {industries.map((ind) => (
              <option key={ind.industry_id} value={ind.industry_id}>
                {ind.industry_name}
              </option>
            ))}
          </select>
        )}
        <p id="industry-hint" className="mt-0.5 text-xs text-slate-500">
          Options are loaded from the backend (manufacturing industries only). Selection drives the compliance profile questionnaire.
        </p>
      </div>
      <button
        type="submit"
        disabled={!isValid}
        className="w-full rounded-xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white shadow-md hover:bg-slate-800 disabled:opacity-50"
      >
        Continue
      </button>
    </form>
  );
}

export function organizationStepDataToApi(
  data: OrganizationStepData
): OnboardingOrganization {
  return {
    organization_name: data.organization_name.trim(),
    unit_name: data.unit_name.trim(),
    address: data.address.trim(),
    state: data.state,
    industry_id: data.industry_id,
  };
}
