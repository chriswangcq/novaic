# Storage-A/B SLA Draft v0.1

## Scope
This SLA applies to:
- `novaic-file-service` (Storage-A)
- `novaic-tool-result-service` (Storage-B)

Effective phase: Week 1 baseline (`v0.1.0-rc1`).

## Service Level Objectives

### 1) Availability
- `novaic-file-service`: >= 99.9% monthly API availability
- `novaic-tool-result-service`: >= 99.9% monthly API availability

Planned maintenance windows are excluded if announced at least 24 hours in advance and kept under 2 hours per month.

### 2) API Latency (excluding client/network edge)
- Read endpoints:
  - P50 <= 80 ms
  - P95 <= 250 ms
  - P99 <= 500 ms
- Write endpoints:
  - P50 <= 120 ms
  - P95 <= 350 ms
  - P99 <= 800 ms

### 3) Durability and Data Protection
- File object durability target (Storage-A object store): >= 99.999999999%
- Metadata/result record durability target: >= 99.99%
- No acknowledged write loss outside declared disaster scenarios.

### 4) Backup and Recovery
- RPO:
  - Metadata/result databases: <= 15 minutes
  - File objects (cross-zone replication + daily consistency snapshot): <= 24 hours worst case
- RTO:
  - Single service restore: <= 60 minutes
  - Cross-service coordinated restore: <= 120 minutes

## Error Budget Policy
- Monthly error budget: 43m 49s (based on 99.9% availability)
- Burn-rate guardrails:
  - > 10% budget in 24h: freeze non-critical deploys
  - > 25% budget in 72h: incident review required before next release
  - > 50% budget in month: reliability-only sprint for remaining cycle

## Incident Severity and Response Targets
- SEV-1 (full outage/data corruption risk):
  - ack <= 5 minutes
  - mitigation start <= 10 minutes
  - stakeholder update every 15 minutes
- SEV-2 (major partial outage/perf regression > 2x SLO):
  - ack <= 15 minutes
  - mitigation start <= 30 minutes
  - update every 30 minutes
- SEV-3 (degraded but workaround exists):
  - ack <= 4 hours
  - fix in next planned release

## SLA Exclusions
- Upstream dependency failures (gateway/runtime/tools) where Storage-A/B is healthy
- Customer misuse violating API contract (oversized payload, invalid auth, abusive retries)
- Force majeure and cloud-wide regional failures outside configured DR topology

## Measurement and Reporting
- Data source: service metrics endpoint + tracing + DB replication lag
- Reporting cadence: daily internal dashboard, weekly reliability summary
- Formal weekly fields:
  - availability by service
  - latency percentile by endpoint class
  - backup job success rate
  - restore drill pass/fail and elapsed time
