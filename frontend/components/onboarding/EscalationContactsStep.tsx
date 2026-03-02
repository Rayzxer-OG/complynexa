"use client";

import { useState } from "react";
import {
  saveEscalationContacts,
  ESCALATION_TRIGGER_OPTIONS,
  type EscalationContactInput,
  type EscalationTriggerValue,
} from "@/lib/api";

const LEVEL_LABELS: Record<1 | 2 | 3, string> = {
  1: "Level 1 – Primary Compliance Owner (required)",
  2: "Level 2 – Secondary Contact (optional)",
  3: "Level 3 – Escalation Authority (optional)",
};

const defaultContact = (level: 1 | 2 | 3): EscalationContactInput => ({
  level,
  name: "",
  email: "",
  mobile: "",
  escalation_trigger: "7_days_before_expiry",
});

interface EscalationContactsStepProps {
  unitId: string;
  submitButtonLabel?: string;
  onSuccess: () => void;
}

export function EscalationContactsStep({ unitId, submitButtonLabel = "Complete Registration", onSuccess }: EscalationContactsStepProps) {
  const [level1, setLevel1] = useState<EscalationContactInput>(defaultContact(1));
  const [level2Enabled, setLevel2Enabled] = useState(false);
  const [level2, setLevel2] = useState<EscalationContactInput>(defaultContact(2));
  const [level3Enabled, setLevel3Enabled] = useState(false);
  const [level3, setLevel3] = useState<EscalationContactInput>(defaultContact(3));
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const buildContacts = (): EscalationContactInput[] => {
    const list: EscalationContactInput[] = [
      {
        ...level1,
        name: level1.name.trim(),
        email: level1.email.trim(),
        mobile: level1.mobile?.trim() || null,
      },
    ];
    if (level2Enabled && (level2.name.trim() || level2.email.trim())) {
      list.push({
        ...level2,
        name: level2.name.trim(),
        email: level2.email.trim(),
        mobile: level2.mobile?.trim() || null,
      });
    }
    if (level3Enabled && (level3.name.trim() || level3.email.trim())) {
      list.push({
        ...level3,
        name: level3.name.trim(),
        email: level3.email.trim(),
        mobile: level3.mobile?.trim() || null,
      });
    }
    return list;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!level1.name.trim() || !level1.email.trim()) {
      setError("Level 1: Full Name and Email are required.");
      return;
    }
    setLoading(true);
    try {
      const contacts = buildContacts();
      await saveEscalationContacts(unitId, contacts);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save escalation contacts");
    } finally {
      setLoading(false);
    }
  };

  const inputClass =
    "w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500";
  const labelClass = "mb-1 block text-sm font-medium text-slate-700";

  const renderLevel = (
    level: 1 | 2 | 3,
    data: EscalationContactInput,
    setData: (d: EscalationContactInput) => void,
    optional = false
  ) => (
    <div className="space-y-3 rounded-xl border border-slate-200 bg-slate-50/50 p-4">
      <p className="text-sm font-semibold text-slate-800">
        {LEVEL_LABELS[level]}
        {optional && " (optional)"}
      </p>
      <div>
        <label htmlFor={`escal-name-${level}`} className={labelClass}>
          Full Name {!optional && <span className="text-red-500">*</span>}
        </label>
        <input
          id={`escal-name-${level}`}
          type="text"
          value={data.name}
          onChange={(e) => setData({ ...data, name: e.target.value })}
          required={!optional}
          className={inputClass}
        />
      </div>
      <div>
        <label htmlFor={`escal-email-${level}`} className={labelClass}>
          Email {!optional && <span className="text-red-500">*</span>}
        </label>
        <input
          id={`escal-email-${level}`}
          type="email"
          value={data.email}
          onChange={(e) => setData({ ...data, email: e.target.value })}
          required={!optional}
          className={inputClass}
        />
      </div>
      <div>
        <label htmlFor={`escal-mobile-${level}`} className={labelClass}>
          Mobile Number
        </label>
        <input
          id={`escal-mobile-${level}`}
          type="tel"
          value={data.mobile ?? ""}
          onChange={(e) => setData({ ...data, mobile: e.target.value || null })}
          className={inputClass}
        />
      </div>
      <div>
        <label htmlFor={`escal-trigger-${level}`} className={labelClass}>
          Escalation delay rule
        </label>
        <select
          id={`escal-trigger-${level}`}
          value={data.escalation_trigger}
          onChange={(e) => setData({ ...data, escalation_trigger: e.target.value as EscalationTriggerValue })}
          className={inputClass}
        >
          {ESCALATION_TRIGGER_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <p className="text-sm text-slate-600">
        Add contacts who will receive compliance expiry reminders. Level 1 is required.
      </p>

      {renderLevel(1, level1, setLevel1, false)}

      <div>
        <button
          type="button"
          onClick={() => setLevel2Enabled(!level2Enabled)}
          className="text-sm font-medium text-slate-700 hover:text-slate-900"
        >
          {level2Enabled ? "− Remove Level 2" : "+ Add Level 2 – Secondary Contact"}
        </button>
        {level2Enabled && <div className="mt-3">{renderLevel(2, level2, setLevel2, true)}</div>}
      </div>

      <div>
        <button
          type="button"
          onClick={() => setLevel3Enabled(!level3Enabled)}
          className="text-sm font-medium text-slate-700 hover:text-slate-900"
        >
          {level3Enabled ? "− Remove Level 3" : "+ Add Level 3 – Escalation Authority"}
        </button>
        {level3Enabled && <div className="mt-3">{renderLevel(3, level3, setLevel3, true)}</div>}
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
        {loading ? "Saving…" : submitButtonLabel}
      </button>
    </form>
  );
}
