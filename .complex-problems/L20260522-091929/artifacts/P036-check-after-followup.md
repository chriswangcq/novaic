# P036 Success Check After Follow-up

## Summary

P036 is solved after follow-up P037. The first execution result `R031` exposed the schema-width gap without switching runtime, and follow-up result `R032` repaired the gap, reran the migration, switched Cortex to Postgres, verified the runtime, and removed the active SQLite residue.

## Evidence

- `R031` documents the safe partial attempt and the original `INTEGER` overflow failure.
- `R032` documents the completed schema repair and production cutover.
- `.complex-problems/L20260522-091929/artifacts/cortex-production-cutover.md` records the final cutover evidence.
- Local and remote compile/test checks passed for the repaired Cortex files.
- The production migration completed with matching source/target counts for all five tables.
- Cortex process args show Postgres operational backend flags after restart.
- Cortex `/health` and `/ready` passed after restart.
- Representative `/v1/scope/history` returned HTTP 200 and `history_backend=postgres`.
- No `operational.sqlite3*` files remain under `/opt/novaic/data/cortex`.
- Rollback archive and central SQLite classification note were updated.

## Criteria Map

- Cortex process starts with Postgres operational backend flags: satisfied by post-restart process args.
- `novaic_cortex` contains matching counts for all five operational tables: satisfied by migration and post-restart count verification.
- Cortex `/health` and `/ready` pass: satisfied after restart.
- Representative operational read smoke passes: satisfied by `/v1/scope/history` HTTP 200.
- No active operational SQLite file remains under `/opt/novaic/data/cortex`: satisfied after no-holder check and active-path cleanup.
- Rollback archive and central classification note are updated: satisfied by `CORTEX_POSTGRES_CUTOVER.md` and the appended classification note.

## Execution Map

- Ticket `T034` produced result `R031`, which was partial and failed the first P036 check.
- Check `C031` created follow-up P037.
- Follow-up ticket `T035` produced result `R032`.
- Check `C032` verified P037 success.
- P036 is judged with `R031` plus `R032`.

## Stress Test

- The first attempt caught a realistic production data-width failure and did not remove the source SQLite file.
- The repair path recovered from the partially created target schema using drop/recreate semantics under `--replace`.
- Startup integration was verified after fixing the missing API deploy and required Cortex API URL argument.
- Cleanup happened only after the service was healthy on Postgres and the old SQLite file had no open holder.

## Residual Risk

- Queue and Entangled remain SQLite-backed and are handled by separate ledger problems.
- The rollback archive is retained, so the old SQLite data exists as recovery evidence but is no longer active state.

## Result IDs

- R031
- R032
