-- Add the 4 conditional (C) compliance requirements for Pharmaceutical and their mapping rows.
-- Your DB has Pharmaceutical with different compliance_name values, so the 4 C types are missing.
-- Run from backend folder: psql -d compliance_tracker -f scripts/add_pharmaceutical_conditional_requirements.sql
-- Or in psql: \i C:/Users/ASUS/Desktop/compliance-tracker-mvp/backend/scripts/add_pharmaceutical_conditional_requirements.sql

-- 1) Insert 4 compliance_requirements for Pharmaceutical (skip if already exist by compliance_code)
INSERT INTO compliance_requirements (
  id, compliance_code, industry, compliance_name, description, risk_weight,
  mandatory, applicability_flag, created_at, updated_at
)
SELECT gen_random_uuid(), 'HAZARDOUS_WASTE', 'Pharmaceutical', 'Hazardous Waste Authorization',
  'Authorization for generation, storage, treatment, and disposal of hazardous waste under the Hazardous Waste Rules.', 20,
  true, 'C', now(), now()
WHERE NOT EXISTS (SELECT 1 FROM compliance_requirements WHERE industry = 'Pharmaceutical' AND compliance_code = 'HAZARDOUS_WASTE');

INSERT INTO compliance_requirements (
  id, compliance_code, industry, compliance_name, description, risk_weight,
  mandatory, applicability_flag, created_at, updated_at
)
SELECT gen_random_uuid(), 'MSIHC', 'Pharmaceutical', 'MSIHC (Manufacturing, Storage, Import of Hazardous Chemicals)',
  'License or consent for handling hazardous chemicals under the MSIHC rules.', 20,
  true, 'C', now(), now()
WHERE NOT EXISTS (SELECT 1 FROM compliance_requirements WHERE industry = 'Pharmaceutical' AND compliance_code = 'MSIHC');

INSERT INTO compliance_requirements (
  id, compliance_code, industry, compliance_name, description, risk_weight,
  mandatory, applicability_flag, created_at, updated_at
)
SELECT gen_random_uuid(), 'PESO_LICENSE', 'Pharmaceutical', 'PESO License',
  'License from the Petroleum and Explosives Safety Organization for storage and handling of petroleum and explosives.', 20,
  true, 'C', now(), now()
WHERE NOT EXISTS (SELECT 1 FROM compliance_requirements WHERE industry = 'Pharmaceutical' AND compliance_code = 'PESO_LICENSE');

INSERT INTO compliance_requirements (
  id, compliance_code, industry, compliance_name, description, risk_weight,
  mandatory, applicability_flag, created_at, updated_at
)
SELECT gen_random_uuid(), 'BOILER_LICENSE', 'Pharmaceutical', 'Boiler License',
  'License for installation and operation of boilers from the Boiler Inspectorate.', 15,
  true, 'C', now(), now()
WHERE NOT EXISTS (SELECT 1 FROM compliance_requirements WHERE industry = 'Pharmaceutical' AND compliance_code = 'BOILER_LICENSE');

-- 2) Insert industry_compliance_mapping rows for those 4 (skip if mapping already exists)
INSERT INTO industry_compliance_mapping (
  id, industry_id, state_id, compliance_requirement_id, applicability_flag,
  condition_key, condition_question, condition_type, risk_weight,
  state_override_possible, override_flag
)
SELECT
  gen_random_uuid(),
  'Pharmaceutical',
  NULL,
  r.id,
  'C',
  CASE r.compliance_code
    WHEN 'HAZARDOUS_WASTE' THEN 'hazardous_waste_generated'
    WHEN 'MSIHC' THEN 'hazardous_chemicals_used'
    WHEN 'PESO_LICENSE' THEN 'petroleum_explosives_stored'
    WHEN 'BOILER_LICENSE' THEN 'boiler_operated'
    ELSE NULL
  END,
  CASE r.compliance_code
    WHEN 'HAZARDOUS_WASTE' THEN 'Does your unit generate hazardous waste?'
    WHEN 'MSIHC' THEN 'Does your unit manufacture, store, or import hazardous chemicals?'
    WHEN 'PESO_LICENSE' THEN 'Does your unit store or handle petroleum or explosives?'
    WHEN 'BOILER_LICENSE' THEN 'Does your unit operate a boiler?'
    ELSE NULL
  END,
  'boolean',
  7,
  false,
  false
FROM compliance_requirements r
WHERE r.industry = 'Pharmaceutical'
  AND r.compliance_code IN ('HAZARDOUS_WASTE', 'MSIHC', 'PESO_LICENSE', 'BOILER_LICENSE')
  AND NOT EXISTS (
    SELECT 1 FROM industry_compliance_mapping m
    WHERE m.industry_id = 'Pharmaceutical'
      AND m.compliance_requirement_id = r.id
      AND m.state_id IS NULL
  );

-- 3) Show result
SELECT industry_id, applicability_flag, condition_key, condition_question
FROM industry_compliance_mapping
WHERE industry_id = 'Pharmaceutical' AND applicability_flag = 'C';
