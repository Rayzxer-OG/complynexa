-- Fix Pharmaceutical conditional (C) rows: set applicability_flag, condition_key, condition_question.
-- Run from backend folder: psql -d compliance_tracker -f scripts/fix_pharmaceutical_c_flags.sql
-- Or in psql: \i C:/Users/ASUS/Desktop/compliance-tracker-mvp/backend/scripts/fix_pharmaceutical_c_flags.sql
--
-- Matches by compliance_name so it works even when compliance_code is NULL.

UPDATE industry_compliance_mapping m
SET
  applicability_flag = 'C',
  condition_key       = c.cond_key,
  condition_question  = c.cond_question,
  condition_type      = 'boolean',
  risk_weight         = 7
FROM (
  SELECT r.id AS req_id,
    c.cond_key,
    c.cond_question
  FROM compliance_requirements r
  JOIN (VALUES
    ('Hazardous Waste Authorization', 'hazardous_waste_generated', 'Does your unit generate hazardous waste?'),
    ('MSIHC (Manufacturing, Storage, Import of Hazardous Chemicals)', 'hazardous_chemicals_used', 'Does your unit manufacture, store, or import hazardous chemicals?'),
    ('PESO License', 'petroleum_explosives_stored', 'Does your unit store or handle petroleum or explosives?'),
    ('Boiler License', 'boiler_operated', 'Does your unit operate a boiler?')
  ) AS c(compliance_name, cond_key, cond_question)
    ON TRIM(r.compliance_name) = c.compliance_name
  WHERE r.industry = 'Pharmaceutical'
) c
WHERE m.industry_id = 'Pharmaceutical'
  AND m.compliance_requirement_id = c.req_id
  AND m.state_id IS NULL;

-- Show result
SELECT industry_id, applicability_flag, condition_key, condition_question
FROM industry_compliance_mapping
WHERE industry_id = 'Pharmaceutical' AND applicability_flag = 'C';
