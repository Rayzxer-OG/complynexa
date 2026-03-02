"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getConditionalQuestions,
  saveComplianceProfile,
  type ConditionalQuestion,
} from "@/lib/api";

interface ComplianceProfileStepProps {
  industryId: string;
  unitId: string;
  submitButtonLabel?: string;
  onNext: () => void;
}

export function ComplianceProfileStep({
  unitId,
  submitButtonLabel = "Continue",
  onNext,
}: ComplianceProfileStepProps) {
  const [questions, setQuestions] = useState<ConditionalQuestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, boolean>>({});

  const loadQuestions = useCallback(() => {
    if (unitId === undefined || unitId === null || unitId === "") {
      setQuestions([]);
      setLoading(false);
      setError("Unit not loaded");
      return;
    }
    setLoading(true);
    setError(null);
    console.log("Fetching conditional for unit:", unitId);
    getConditionalQuestions(unitId)
      .then((data) => {
        console.log("Conditional response:", data);
        const questionsList = Array.isArray(data) ? data : [];
        setQuestions(questionsList);
        setAnswers((prev) => {
          const next = { ...prev };
          questionsList.forEach((q) => {
            if (q && q.compliance_requirement_id && !(q.compliance_requirement_id in next))
              next[q.compliance_requirement_id] = false;
          });
          return next;
        });
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load questions"))
      .finally(() => setLoading(false));
  }, [unitId]);

  useEffect(() => {
    loadQuestions();
  }, [loadQuestions]);

  const handleChange = (complianceRequirementId: string, value: boolean) => {
    setAnswers((prev) => ({ ...prev, [complianceRequirementId]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (unitId === undefined || unitId === null || unitId === "") {
      setError("Unit not loaded");
      return;
    }
    setError(null);
    setSaving(true);
    try {
      await saveComplianceProfile(
        unitId,
        questions.map((q) => ({
          compliance_requirement_id: q.compliance_requirement_id,
          applies: answers[q.compliance_requirement_id] ?? false,
        }))
      );
      onNext();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const inputClass =
    "h-4 w-4 rounded border-slate-300 text-slate-900 focus:ring-slate-500";
  const labelClass = "ml-2 text-sm font-medium text-slate-700";

  if (unitId === undefined || unitId === null || unitId === "") {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50/50 py-6 px-4 text-center">
        <p className="font-medium text-red-800">Unit not loaded</p>
        <p className="mt-1 text-sm text-red-700">
          Cannot load conditional questions without a unit. Please go back and complete unit creation first.
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="py-4 text-sm text-slate-500">
        Loading compliance profile questions…
      </div>
    );
  }

  if (questions.length === 0) {
    return (
      <div className="space-y-4">
        <p className="text-sm text-slate-600">
          No conditional compliance questions for this unit. You can proceed.
        </p>
        {error && (
          <p className="text-sm text-red-600" role="alert">
            {error}
          </p>
        )}
        <button
          type="button"
          disabled={saving}
          onClick={async () => {
            setError(null);
            setSaving(true);
            try {
              await saveComplianceProfile(unitId, []);
              onNext();
            } catch (err) {
              setError(err instanceof Error ? err.message : "Failed to save");
            } finally {
              setSaving(false);
            }
          }}
          className="w-full rounded-xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white shadow-md hover:bg-slate-800 disabled:opacity-50"
        >
          {saving ? "Saving…" : submitButtonLabel}
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <p className="text-sm text-slate-600">
        Answer the following to determine which compliances apply to your unit.
      </p>
      <div className="space-y-4">
        {questions.map((q) => (
          <div
            key={q.compliance_requirement_id}
            className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50/50 px-4 py-3"
          >
            <div className="flex flex-1 flex-col">
              <span className="text-sm font-medium text-slate-800">{q.compliance_name}</span>
              <span className="text-sm text-slate-600 mt-0.5">{q.conditional_question}</span>
            </div>
            <div className="ml-4 flex shrink-0 gap-4">
              <label className="inline-flex items-center">
                <input
                  id={`profile-${q.compliance_requirement_id}-yes`}
                  type="radio"
                  name={q.compliance_requirement_id}
                  checked={answers[q.compliance_requirement_id] === true}
                  onChange={() => handleChange(q.compliance_requirement_id, true)}
                  className={inputClass}
                />
                <span className={labelClass}>Yes</span>
              </label>
              <label className="inline-flex items-center">
                <input
                  id={`profile-${q.compliance_requirement_id}-no`}
                  type="radio"
                  name={q.compliance_requirement_id}
                  checked={answers[q.compliance_requirement_id] === false}
                  onChange={() => handleChange(q.compliance_requirement_id, false)}
                  className={inputClass}
                />
                <span className={labelClass}>No</span>
              </label>
            </div>
          </div>
        ))}
      </div>
      {error && (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
      <button
        type="submit"
        disabled={saving}
        className="w-full rounded-xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white shadow-md hover:bg-slate-800 disabled:opacity-50"
      >
        {saving ? "Saving…" : submitButtonLabel}
      </button>
    </form>
  );
}
