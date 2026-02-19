# Effective Compatibility Counting Rule

## Effective Rule Reference
- effective_rule_id: `compat-count-v1`
- effective_rule_doc: `ops-rounds/governance/compatibility-consumption-counting-rule.md`
- effective_since: `2026-02-20`
- supersedes: round-specific counting interpretations

## Enforcement Scope
- CI compatibility gate must validate the rule markers and unique component threshold.
- Governance reports must reference this effective rule when claiming `>=5` compatibility consumption.
- Stable index reference:
  - `ops-rounds/governance/governance-index.md`

## Audit Note
- Any rule update must:
  1) publish a new rule ID/version
  2) update this effective reference file
  3) update CI validation accordingly
