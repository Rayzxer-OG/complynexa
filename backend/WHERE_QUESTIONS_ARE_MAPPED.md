# Where compliance conditional questions are mapped

Use this as a checklist to verify industry conditional questions (e.g. for Pharmaceutical) end-to-end.

---

## 1. Backend: API that returns questions

**File:** `app/api/v1/industries.py`

- **Function:** `get_industry_conditional_questions(industry_id, db)`
- **Route:** `GET /api/v1/industries/conditional-questions/{industry_id}`
- **Logic:** Queries `industry_compliance_mapping` where:
  - `industry_id` = request path param (e.g. `"Pharmaceutical"`)
  - `state_id IS NULL`
  - `applicability_flag = 'C'`
  - `condition_key` and `condition_question` are not empty
- **Returns:** List of `{ "condition_key", "question", "type" }`.

---

## 2. Backend: Table that stores the mapping

**Table:** `industry_compliance_mapping`

- **Model:** `app/models/industry_compliance_mapping.py` — `IndustryComplianceMapping`
- **Relevant columns:** `industry_id`, `state_id`, `compliance_requirement_id`, `applicability_flag`, `condition_key`, `condition_question`, `condition_type`
- **Conditional questions:** Rows with `applicability_flag = 'C'` and non-null `condition_key` / `condition_question`.

---

## 3. Backend: Where the mapping data is seeded

**File:** `alembic/versions/033_seed_industry_compliance_mapping_manufacturing.py`

- **What it does:** Inserts rows into `industry_compliance_mapping` for each industry in `INDUSTRY_MATRIX`.
- **Pharmaceutical:** In `INDUSTRY_MATRIX["Pharmaceutical"]` you’ll see entries like:
  - `("HAZARDOUS_WASTE", "C", 7)`
  - `("MSIHC", "C", 7)`
  - `("PESO_LICENSE", "C", 7)`
  - `("BOILER_LICENSE", "C", 7)`
- **Condition text:** `CONDITION_FOR_C` in the same file maps compliance codes to `(condition_key, condition_question)` for these C entries.
- **Important:** This migration depends on `compliance_requirements` already having rows with matching `industry` and `compliance_code` (from migration `032_seed_manufacturing_compliance_master.py`).

**To confirm data:**

- Run: `alembic upgrade head` (so 032 and 033 are applied).
- In DB:
  - `SELECT industry_id, applicability_flag, condition_key, condition_question FROM industry_compliance_mapping WHERE industry_id = 'Pharmaceutical' AND applicability_flag = 'C';`
- You should see 4 rows for Pharmaceutical (or more if your matrix has more C items).

---

## 4. Industries master (IDs used in the mapping)

**File:** `alembic/versions/030_industries_master_table.py`

- **Table:** `industries`
- **Pharmaceutical:** Inserted with `industry_id = 'Pharmaceutical'`, `industry_name = 'Pharmaceutical'`.
- The same string `"Pharmaceutical"` must be used:
  - In `industries.industry_id`
  - In `industry_compliance_mapping.industry_id`
  - In `units.industry` when creating a unit (onboarding).

---

## 5. Frontend: Where the API is called

- **Client:** `frontend/lib/api.ts` — `getIndustryConditionalQuestions(industryId)`
  - Builds URL: `/api/industries/conditional-questions/${encodeURIComponent(industryId)}`
- **Next.js proxy:** `frontend/app/api/industries/conditional-questions/[industryId]/route.ts`
  - Forwards to backend: `{API_URL}/api/v1/industries/conditional-questions/{industryId}`
- **Usage:**  
  - Onboarding step 3: `frontend/components/onboarding/ComplianceProfileStep.tsx` (prop `industryId` from `organization.industry_id`).  
  - Checklist page: `frontend/app/compliance-checklist/page.tsx` (uses `unitInfo.industry` to load industry questions).

---

## Quick manual check

1. **Backend running:** `GET http://localhost:8000/api/v1/industries/conditional-questions/Pharmaceutical`  
   - Should return JSON array of 4 objects (or your current C count) with `condition_key`, `question`, `type`.
2. **DB:**  
   - `SELECT * FROM industry_compliance_mapping WHERE industry_id = 'Pharmaceutical' AND applicability_flag = 'C';`  
   - Expect 4 rows (or more if you added more C items).
3. **Migrations:**  
   - `alembic current`  
   - Ensure revision is at least 033 (after 030, 031, 032, 033).

If the backend URL above returns 404, the FastAPI route or prefix is wrong. If it returns `[]`, the mapping table is empty or `industry_id` / `applicability_flag` don’t match — fix or re-run the seed migration.
