"use client";

import { useEffect, useState } from "react";
import { setUnitId } from "@/lib/auth";
import {
  createOrganization,
  getIndustries,
  getBusinessTypes,
  type OrganizationCreateBody,
  type Industry,
  type BusinessType,
} from "@/lib/api";

interface FactoryStepProps {
  onSuccess: () => void;
}

export function FactoryStep({ onSuccess }: FactoryStepProps) {
  const [organizationName, setOrganizationName] = useState("");
  const [unitName, setUnitName] = useState("");
  const [address, setAddress] = useState("");
  const [state, setState] = useState("");
  const [industry, setIndustry] = useState("");
  const [businessType, setBusinessType] = useState("");
  const [employees, setEmployees] = useState("");
  const [manufacturing, setManufacturing] = useState<boolean>(true);
  const [electricalLoad, setElectricalLoad] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [industries, setIndustries] = useState<Industry[]>([]);
  const [industriesLoading, setIndustriesLoading] = useState(true);
  const [industriesError, setIndustriesError] = useState<string | null>(null);
  const [businessTypes, setBusinessTypes] = useState<BusinessType[]>([]);
  const [businessTypesLoading, setBusinessTypesLoading] = useState(true);
  const [businessTypesError, setBusinessTypesError] = useState<string | null>(null);

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

  useEffect(() => {
    let cancelled = false;
    setBusinessTypesLoading(true);
    setBusinessTypesError(null);
    getBusinessTypes()
      .then((list) => {
        if (!cancelled) setBusinessTypes(list);
      })
      .catch((e) => {
        if (!cancelled) setBusinessTypesError(e instanceof Error ? e.message : "Failed to load business types");
      })
      .finally(() => {
        if (!cancelled) setBusinessTypesLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const result = await createOrganization({
        organization_name: organizationName,
        unit_name: unitName,
        address,
        state,
        industry,
        business_type: businessType,
        employees: parseInt(employees, 10) || 0,
        manufacturing,
        electrical_load: parseFloat(electricalLoad) || 0,
      } as OrganizationCreateBody);
      if (result.unit_id) setUnitId(result.unit_id);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save details");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="organizationName" className="mb-1 block text-sm font-medium text-slate-700">
          Organization Name <span className="text-red-500">*</span>
        </label>
        <input
          id="organizationName"
          type="text"
          value={organizationName}
          onChange={(e) => setOrganizationName(e.target.value)}
          required
          className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        />
      </div>
      <div>
        <label htmlFor="unitName" className="mb-1 block text-sm font-medium text-slate-700">
          Unit Name <span className="text-red-500">*</span>
        </label>
        <input
          id="unitName"
          type="text"
          value={unitName}
          onChange={(e) => setUnitName(e.target.value)}
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
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          required
          className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        />
      </div>
      <div>
        <label htmlFor="state" className="mb-1 block text-sm font-medium text-slate-700">
          State <span className="text-red-500">*</span>
        </label>
        <input
          id="state"
          type="text"
          value={state}
          onChange={(e) => setState(e.target.value)}
          required
          className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        />
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
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
            required
            className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
          >
            <option value="">Select manufacturing industry</option>
            {industries.map((ind) => (
              <option key={ind.industry_id} value={ind.industry_id}>
                {ind.industry_name}
              </option>
            ))}
          </select>
        )}
      </div>
      <div>
        <label htmlFor="businessType" className="mb-1 block text-sm font-medium text-slate-700">
          Business Type <span className="text-red-500">*</span>
        </label>
        {businessTypesLoading ? (
          <div className="w-full rounded-xl border border-slate-300 bg-slate-50 px-3 py-2.5 text-sm text-slate-500">
            Loading business types…
          </div>
        ) : businessTypesError ? (
          <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700" role="alert">
            {businessTypesError}
          </div>
        ) : (
          <select
            id="businessType"
            value={businessType}
            onChange={(e) => setBusinessType(e.target.value)}
            required
            className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
          >
            <option value="">Select</option>
            {businessTypes.map((bt) => (
              <option key={bt.business_type_id} value={bt.business_type_id}>
                {bt.business_type_name}
              </option>
            ))}
          </select>
        )}
      </div>
      <div>
        <label htmlFor="employees" className="mb-1 block text-sm font-medium text-slate-700">
          Number of Employees <span className="text-red-500">*</span>
        </label>
        <input
          id="employees"
          type="number"
          min={0}
          value={employees}
          onChange={(e) => setEmployees(e.target.value)}
          required
          className="w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        />
      </div>
      <div>
        <span className="mb-1 block text-sm font-medium text-slate-700">
          Manufacturing Activity <span className="text-red-500">*</span>
        </span>
        <div className="flex gap-4 pt-1">
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="manufacturing"
              checked={manufacturing === true}
              onChange={() => setManufacturing(true)}
              className="h-4 w-4 text-slate-800"
            />
            <span className="text-sm">Yes</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="manufacturing"
              checked={manufacturing === false}
              onChange={() => setManufacturing(false)}
              className="h-4 w-4 text-slate-800"
            />
            <span className="text-sm">No</span>
          </label>
        </div>
      </div>
      <div>
        <label htmlFor="electricalLoad" className="mb-1 block text-sm font-medium text-slate-700">
          Connected Electrical Load (kW) <span className="text-red-500">*</span>
        </label>
        <input
          id="electricalLoad"
          type="number"
          min={0}
          step={0.1}
          value={electricalLoad}
          onChange={(e) => setElectricalLoad(e.target.value)}
          required
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
        disabled={loading}
        className="w-full rounded-xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white shadow-md hover:bg-slate-800 disabled:opacity-50"
      >
        {loading ? "Saving…" : "Continue"}
      </button>
    </form>
  );
}
