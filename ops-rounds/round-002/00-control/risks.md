# Round 002 Risks

## Active Risks

1. **Runtime startup healthcheck instability**  
   - Severity: P1  
   - Owner: Runtime Team  
   - Mitigation: isolate failing startup path, add startup smoke command, prove pass with repeat runs.
   - Latest: startup contract fixed and verified with 3/3 repeat passes (see `20-reports/runtime-startup-verification-report.md`).

2. **Storage delivery is document-heavy, code-light (partially mitigated)**  
   - Severity: P1  
   - Owner: Storage-A/B  
   - Mitigation: executable backup/restore/validation scripts delivered; next close CI smoke and contract diff evidence.
   - Evidence:
     - `novaic-backend/scripts/storage_ab_backup.sh`
     - `novaic-backend/scripts/storage_ab_restore.sh`
     - `novaic-backend/scripts/storage_ab_validate_restore.sh`
     - `ops-rounds/round-002/20-reports/team-storage-ab-validation-latest.md`

3. **Shared-kernel still in bridge mode**  
   - Severity: P1  
   - Owner: Platform Team  
   - Mitigation: migrate real shared modules and reduce bridge dependency in target components.

4. **Desktop RC and clean-machine validation missing**  
   - Severity: P1  
   - Owner: Desktop Team  
   - Mitigation: produce installer artifact and repeatable validation checklist.

5. **Worker idempotency incomplete across process boundaries**  
   - Severity: P1  
   - Owner: Agent Runtime Team  
   - Mitigation: persistent dedup strategy or queue-level retry window fields.

6. **Tools reliability lacks stress proof**  
   - Severity: P1  
   - Owner: Tools Team  
   - Mitigation: run and report deterministic timeout and concurrency stress tests.

## Escalation Rule
- Any risk upgraded to P0 must be reported in daily sync and captured in `30-review/reviewer-findings.md` within the same day.
