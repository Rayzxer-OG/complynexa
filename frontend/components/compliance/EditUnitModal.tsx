"use client";

import { useState, useEffect } from "react";
import { updateUnit, getIndustries, type UnitInfo, type UnitUpdatePayload, type Industry } from "@/lib/api";

const inputClass =
  "w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500";
const labelClass = "mb-1 block text-sm font-medium text-slate-700";

export function EditUnitModal({
  unitId,
  unit,
  open,
  onClose,
  onSuccess,
}: {
  unitId: string;
  unit: UnitInfo | null;
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [industryId, setIndustryId] = useState<string>("");
  const [industries, setIndustries] = useState<Industry[]>([]);
  const [industriesLoading, setIndustriesLoading] = useState(false);
  const [employeeCount, setEmployeeCount] = useState<string>("");
  const [hazardousFlag, setHazardousFlag] = useState(false);
  const [boilerFlag, setBoilerFlag] = useState(false);
  const [electricalLoad, setElectricalLoad] = useState<string>("");
  const [builtUpArea, setBuiltUpArea] = useState<string>("");
  const [spcbCategory, setSpcbCategory] = useState<string>("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setIndustriesLoading(true);
    getIndustries()
      .then(setIndustries)
      .catch(() => setIndustries([]))
      .finally(() => setIndustriesLoading(false));
  }, [open]);

  useEffect(() => {
    if (!unit) return;
    setIndustryId(unit.industry ?? "");
    setEmployeeCount(String(unit.employee_count ?? ""));
    setHazardousFlag(unit.hazardous_flag ?? false);
    setBoilerFlag(unit.boiler_flag ?? false);
    setElectricalLoad(unit.electrical_load != null ? String(unit.electrical_load) : "");
    setBuiltUpArea(unit.built_up_area != null ? String(unit.built_up_area) : "");
    setSpcbCategory(unit.spcb_category ?? "");
  }, [unit, open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const payload: UnitUpdatePayload = {};
      if (industryId.trim() !== "") payload.industry = industryId.trim();
      if (employeeCount !== "") payload.employee_count = parseInt(employeeCount, 10) || 0;
      payload.hazardous_flag = hazardousFlag;
      payload.boiler_flag = boilerFlag;
      if (electricalLoad !== "") payload.electrical_load = parseFloat(electricalLoad) || 0;
      if (builtUpArea !== "") payload.built_up_area = parseFloat(builtUpArea) ?? undefined;
      if (spcbCategory.trim() !== "") payload.spcb_category = spcbCategory.trim();
      else payload.spcb_category = null;
      await updateUnit(unitId, payload);
      onSuccess();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to update unit");
    } finally {
      setSaving(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white shadow-xl">
        <div className="border-b border-slate-200 px-4 py-3">
          <h2 className="text-lg font-semibold text-slate-900">Edit unit profile</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Changes may add or remove compliance requirements. Checklist will refresh automatically.
          </p>
        </div>
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div>
            <label htmlFor="edit-industry" className={labelClass}>
              Industry
            </label>
            {industriesLoading ? (
              <div className="rounded-xl border border-slate-300 bg-slate-50 px-3 py-2.5 text-sm text-slate-500">
                Loading industries…
              </div>
            ) : (
              <select
                id="edit-industry"
                value={industryId}
                onChange={(e) => setIndustryId(e.target.value)}
                className={inputClass}
              >
                <option value="">Not set / Select industry</option>
                {industries.map((ind) => (
                  <option key={ind.industry_id} value={ind.industry_id}>
                    {ind.industry_name}
                  </option>
                ))}
              </select>
            )}
            <p className="mt-0.5 text-xs text-slate-500">
              Required for compliance checklist. Select the industry that matches your unit.
            </p>
          </div>
          <div>
            <label htmlFor="edit-employee-count" className={labelClass}>
              Employee count
            </label>
            <input
              id="edit-employee-count"
              type="number"
              min={0}
              value={employeeCount}
              onChange={(e) => setEmployeeCount(e.target.value)}
              className={inputClass}
            />
          </div>
          <div>
            <label htmlFor="edit-electrical-load" className={labelClass}>
              Electrical load (kW)
            </label>
            <input
              id="edit-electrical-load"
              type="number"
              min={0}
              step="any"
              value={electricalLoad}
              onChange={(e) => setElectricalLoad(e.target.value)}
              className={inputClass}
            />
          </div>
          <div>
            <label htmlFor="edit-built-up-area" className={labelClass}>
              Built-up area
            </label>
            <input
              id="edit-built-up-area"
              type="number"
              min={0}
              step="any"
              value={builtUpArea}
              onChange={(e) => setBuiltUpArea(e.target.value)}
              className={inputClass}
            />
          </div>
          <div>
            <label htmlFor="edit-spcb-category" className={labelClass}>
              SPCB category
            </label>
            <input
              id="edit-spcb-category"
              type="text"
              placeholder="e.g. Red, Orange, Green"
              value={spcbCategory}
              onChange={(e) => setSpcbCategory(e.target.value)}
              className={inputClass}
            />
          </div>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={hazardousFlag}
                onChange={(e) => setHazardousFlag(e.target.checked)}
                className="rounded border-slate-300"
              />
              <span className="text-sm text-slate-700">Hazardous waste / hazardous flag</span>
            </label>
          </div>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={boilerFlag}
                onChange={(e) => setBoilerFlag(e.target.checked)}
                className="rounded border-slate-300"
              />
              <span className="text-sm text-slate-700">Boiler present</span>
            </label>
          </div>
          {error && (
            <p className="text-sm text-red-600" role="alert">
              {error}
            </p>
          )}
          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50"
            >
              {saving ? "Saving…" : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
