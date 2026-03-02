"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  getUnit,
  getEscalationContacts,
  saveEscalationContacts,
  ESCALATION_TRIGGER_DAYS_OPTIONS,
  type UnitInfo,
  type EscalationContactInput,
  type EscalationContactResponse,
} from "@/lib/api";
import { getToken, getUnitId } from "@/lib/auth";

const LEVEL_LABELS: Record<1 | 2 | 3, string> = {
  1: "Level 1 – Primary Compliance Owner (required)",
  2: "Level 2 – Secondary Contact (optional)",
  3: "Level 3 – Escalation Authority (optional)",
};

function contactFromResponse(c: EscalationContactResponse, level: 1 | 2 | 3): EscalationContactInput {
  const defaultDays = level === 1 ? 30 : level === 2 ? 7 : 0;
  return {
    level,
    name: c.name,
    email: c.email,
    mobile: c.mobile ?? null,
    escalation_trigger_days: c.escalation_trigger_days ?? defaultDays,
    escalation_trigger: c.escalation_trigger as EscalationContactInput["escalation_trigger"],
  };
}

const defaultContact = (level: 1 | 2 | 3): EscalationContactInput => ({
  level,
  name: "",
  email: "",
  mobile: null,
  escalation_trigger_days: level === 1 ? 30 : level === 2 ? 7 : 0,
});

export default function UnitSettingsPage() {
  const router = useRouter();
  const [allowed, setAllowed] = useState(false);
  const [unitId, setUnitId] = useState<string | null>(null);
  const [unitInfo, setUnitInfo] = useState<UnitInfo | null>(null);
  const [level1, setLevel1] = useState<EscalationContactInput>(defaultContact(1));
  const [level2Enabled, setLevel2Enabled] = useState(false);
  const [level2, setLevel2] = useState<EscalationContactInput>(defaultContact(2));
  const [level3Enabled, setLevel3Enabled] = useState(false);
  const [level3, setLevel3] = useState<EscalationContactInput>(defaultContact(3));
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const loadData = useCallback(() => {
    const uid = getUnitId();
    if (!uid) {
      setLoading(false);
      return;
    }
    setUnitId(uid);
    setLoading(true);
    setError(null);
    Promise.all([getUnit(uid), getEscalationContacts(uid)])
      .then(([unit, contacts]) => {
        setUnitInfo(unit);
        const byLevel = contacts.reduce(
          (acc, c) => {
            if (!acc[c.level]) acc[c.level] = c;
            return acc;
          },
          {} as Record<number, EscalationContactResponse>
        );
        if (byLevel[1]) setLevel1(contactFromResponse(byLevel[1], 1));
        if (byLevel[2]) {
          setLevel2Enabled(true);
          setLevel2(contactFromResponse(byLevel[2], 2));
        }
        if (byLevel[3]) {
          setLevel3Enabled(true);
          setLevel3(contactFromResponse(byLevel[3], 3));
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    setAllowed(true);
    loadData();
  }, [router, loadData]);

  const buildContacts = (): EscalationContactInput[] => {
    const list: EscalationContactInput[] = [
      {
        ...level1,
        name: level1.name.trim(),
        email: level1.email.trim(),
        mobile: level1.mobile?.trim() || null,
        escalation_trigger_days: level1.escalation_trigger_days ?? 30,
      },
    ];
    if (level2Enabled && (level2.name.trim() || level2.email.trim())) {
      list.push({
        ...level2,
        name: level2.name.trim(),
        email: level2.email.trim(),
        mobile: level2.mobile?.trim() || null,
        escalation_trigger_days: level2.escalation_trigger_days ?? 7,
      });
    }
    if (level3Enabled && (level3.name.trim() || level3.email.trim())) {
      list.push({
        ...level3,
        name: level3.name.trim(),
        email: level3.email.trim(),
        mobile: level3.mobile?.trim() || null,
        escalation_trigger_days: level3.escalation_trigger_days ?? 0,
      });
    }
    return list;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!unitId) return;
    setError(null);
    setSuccess(false);
    if (!level1.name.trim() || !level1.email.trim()) {
      setError("Level 1: Full Name and Email are required.");
      return;
    }
    setSaving(true);
    try {
      const contacts = buildContacts();
      await saveEscalationContacts(unitId, contacts);
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
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
        <label htmlFor={`escal-trigger-days-${level}`} className={labelClass}>
          Notify when (days before expiry)
        </label>
        <select
          id={`escal-trigger-days-${level}`}
          value={data.escalation_trigger_days ?? (level === 1 ? 30 : level === 2 ? 7 : 0)}
          onChange={(e) =>
            setData({
              ...data,
              escalation_trigger_days: parseInt(e.target.value, 10),
            })
          }
          className={inputClass}
        >
          {ESCALATION_TRIGGER_DAYS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );

  if (!allowed) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-slate-500">
        Loading…
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-6 lg:px-8">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-slate-900">Unit Settings</h1>
          <Link
            href="/dashboard"
            className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Back to Dashboard
          </Link>
        </div>

        {unitInfo && (
          <div className="rounded-xl border border-slate-200 bg-slate-800 px-4 py-4 text-white">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-300">Unit</p>
            <p className="mt-1 text-lg font-semibold text-white">{unitInfo.unit_name}</p>
            <p className="mt-0.5 text-sm text-slate-200">{unitInfo.address}</p>
          </div>
        )}

        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Escalation contacts</h2>
          <p className="mt-1 text-sm text-slate-600">
            Compliance expiry reminders are sent to these contacts by level: 30/15 days → Level 1,
            7/3 days → Level 2, on expiry → Level 3. Level 1 is required.
          </p>

          {loading ? (
            <p className="mt-4 text-sm text-slate-500">Loading…</p>
          ) : (
            <form onSubmit={handleSubmit} className="mt-6 space-y-6">
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
              {success && (
                <p className="text-sm text-emerald-600" role="status">
                  Escalation contacts saved.
                </p>
              )}

              <button
                type="submit"
                disabled={saving}
                className="w-full rounded-xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white shadow-md hover:bg-slate-800 disabled:opacity-50"
              >
                {saving ? "Saving…" : "Save escalation contacts"}
              </button>
            </form>
          )}
        </section>
      </div>
    </div>
  );
}
