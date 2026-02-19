# Compatibility Consumption Counting Rule (Official v1)

## Purpose
Standardize how `>=5` compatibility-consumption evidence is counted, audited, and enforced.

## Rule ID
- `compat-count-v1`

## Counting Rule
To count as one valid component consumption item, all conditions must be met:
1. component is declared in `compatibility.yaml` under `repos.id`
2. evidence includes exact workflow/file reference that enforces compatibility check
3. evidence includes check detail describing how failure blocks delivery

`>=5` requirement is met only when there are at least 5 unique components satisfying all three conditions.

## Accepted Evidence Path Policy (Evergreen)
- canonical latest evidence path:
  - `ops-rounds/governance/compatibility-consumption-evidence-latest.md`
- round-specific reports may reference this file, but CI validates this evergreen path.

## Required Evidence Markers
The evidence file must include:
- `counting_rule_id: compat-count-v1`
- `counting_rule_version: v1`
- `evidence_path_policy: evergreen`
- `unique_component_count: <n>`
- `component_count_check: PASS` (only valid when `n >= 5`)

## Ownership
- Platform Team owns rule maintenance.
- Reviewer owns final audit interpretation.

## Effective Reference
- effective rule pointer:
  - `ops-rounds/governance/effective-compatibility-counting-rule.md`
