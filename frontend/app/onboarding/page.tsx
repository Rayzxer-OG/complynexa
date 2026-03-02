"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AccountStep } from "@/components/onboarding/AccountStep";
import { ComplianceProfileStep } from "@/components/onboarding/ComplianceProfileStep";
import {
  OrganizationStep,
  organizationStepDataToApi,
  type OrganizationStepData,
} from "@/components/onboarding/OrganizationStep";
import type { AccountStepData } from "@/components/onboarding/AccountStep";
import { EscalationContactsStep } from "@/components/onboarding/EscalationContactsStep";
import { SuccessStep } from "@/components/onboarding/SuccessStep";

const STEPS = [
  { id: 1, label: "Organization Details" },
  { id: 2, label: "Admin Account" },
  { id: 3, label: "Compliance Profile" },
  { id: 4, label: "Escalation Contacts" },
  { id: 5, label: "Success" },
];

const FINAL_STEP = 4;

/** Submit button label by step index: continue to next step name, or "Complete Registration" on final step. */
function getSubmitButtonLabel(currentStep: number): string {
  if (currentStep === FINAL_STEP) return "Complete Registration";
  if (currentStep === 2) return "Continue to Compliance Profile";
  if (currentStep === 3) return "Continue to Escalation Contacts";
  return "Continue";
}

const defaultOrganization: OrganizationStepData = {
  organization_name: "",
  unit_name: "",
  address: "",
  state: "",
  industry_id: "",
};

const defaultAccount: AccountStepData = {
  full_name: "",
  email: "",
  mobile: "",
  password: "",
  alternate_email: "",
  alternate_mobile: "",
};

export default function OnboardingPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [mounted, setMounted] = useState(false);
  const [organization, setOrganization] = useState<OrganizationStepData>(defaultOrganization);
  const [account, setAccount] = useState<AccountStepData>(defaultAccount);
  const [onboardingUnitId, setOnboardingUnitId] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="text-sm text-slate-500">Loading…</div>
      </div>
    );
  }

  const organizationPayload = organizationStepDataToApi(organization);

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4">
      <div className="mx-auto max-w-[500px]">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-lg shadow-slate-200/50 sm:p-8">
          <div className="mb-8">
            <div className="flex items-center justify-between">
              {STEPS.map((step, index) => (
                <div key={step.id} className="flex flex-1 items-center">
                  <div
                    className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-sm font-semibold ${
                      currentStep >= step.id
                        ? "bg-slate-900 text-white"
                        : "bg-slate-200 text-slate-500"
                    }`}
                  >
                    {step.id}
                  </div>
                  {index < STEPS.length - 1 && (
                    <div
                      className={`mx-1 h-0.5 flex-1 sm:mx-2 ${
                        currentStep > step.id ? "bg-slate-900" : "bg-slate-200"
                      }`}
                    />
                  )}
                </div>
              ))}
            </div>
            <div className="mt-2 flex justify-between text-xs font-medium text-slate-500">
              {STEPS.map((step) => (
                <span key={step.id}>{step.label}</span>
              ))}
            </div>
          </div>

          {currentStep === 1 && (
            <>
              <h1 className="mb-6 text-lg font-semibold text-slate-900">
                Organization Details
              </h1>
              <OrganizationStep
                data={organization}
                onChange={setOrganization}
                onNext={() => setCurrentStep(2)}
              />
            </>
          )}
          {currentStep === 2 && (
            <>
              <h1 className="mb-6 text-lg font-semibold text-slate-900">
                Admin Account
              </h1>
              <AccountStep
                data={account}
                onChange={setAccount}
                organizationPayload={organizationPayload}
                submitButtonLabel={getSubmitButtonLabel(2)}
                onSuccess={(result) => {
                  const unitId = result?.unit_id;
                  if (unitId !== undefined && unitId !== null && unitId !== "") {
                    setOnboardingUnitId(unitId);
                    setCurrentStep(3);
                  } else {
                    router.replace("/compliance-checklist");
                    router.refresh();
                  }
                }}
              />
            </>
          )}
          {currentStep === 3 && onboardingUnitId && organization.industry_id && (
            <>
              <h1 className="mb-6 text-lg font-semibold text-slate-900">
                Compliance Profile Setup
              </h1>
              <ComplianceProfileStep
                industryId={organization.industry_id}
                unitId={onboardingUnitId}
                submitButtonLabel={getSubmitButtonLabel(3)}
                onNext={() => setCurrentStep(4)}
              />
            </>
          )}
          {currentStep === 4 && onboardingUnitId && (
            <>
              <h1 className="mb-6 text-lg font-semibold text-slate-900">
                Compliance Escalation Contacts
              </h1>
              <EscalationContactsStep
                unitId={onboardingUnitId}
                submitButtonLabel={getSubmitButtonLabel(4)}
                onSuccess={() => setCurrentStep(5)}
              />
            </>
          )}
          {currentStep === 5 && <SuccessStep unitId={onboardingUnitId} />}
        </div>
      </div>
    </div>
  );
}
