"use client";

import { useState } from "react";
import type { ConditionalQuestion } from "@/lib/api";
import { saveComplianceAttribute } from "@/lib/api";

export function ConditionalQuestionsCard({
  unitId,
  questions,
  onAnswerSaved,
}: {
  unitId: string;
  questions: ConditionalQuestion[];
  onAnswerSaved: () => void;
}) {
  const [submitting, setSubmitting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnswer = async (
    complianceRequirementId: string,
    applies: boolean
  ) => {
    setError(null);
    setSubmitting(complianceRequirementId);
    try {
      await saveComplianceAttribute(unitId, complianceRequirementId, applies);
      onAnswerSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save answer");
    } finally {
      setSubmitting(null);
    }
  };

  const onYesNoClick = (e: React.MouseEvent, complianceRequirementId: string, applies: boolean) => {
    e.preventDefault();
    void handleAnswer(complianceRequirementId, applies);
  };

  if (questions.length === 0) return null;

  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50/50 shadow-sm overflow-hidden">
      <div className="bg-amber-100/80 px-4 py-3 border-b border-amber-200">
        <p className="text-xs font-semibold uppercase tracking-wider text-amber-800">
          Conditional compliance
        </p>
        <p className="mt-0.5 text-sm text-amber-700">
          Answer these to show or hide requirements in your checklist.
        </p>
      </div>
      <div className="px-4 py-4 space-y-4">
        {error && (
          <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-md">
            {error}
          </p>
        )}
        {questions.map((q) => (
          <div
            key={q.compliance_requirement_id}
            className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-lg border border-amber-200/80 bg-white px-4 py-3"
          >
            <div>
              <p className="font-medium text-slate-800">{q.compliance_name}</p>
              <p className="text-sm text-slate-600 mt-0.5">
                {q.conditional_question}
              </p>
            </div>
            <div className="flex gap-2 shrink-0">
              <button
                type="button"
                disabled={submitting !== null}
                onClick={(e) => onYesNoClick(e, q.compliance_requirement_id, true)}
                className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Yes
              </button>
              <button
                type="button"
                disabled={submitting !== null}
                onClick={(e) => onYesNoClick(e, q.compliance_requirement_id, false)}
                className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                No
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
