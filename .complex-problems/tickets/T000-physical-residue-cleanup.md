# T000: Physical Residue Cleanup After Generic Worker Substrate Migration

Status: done
Problem: P000

## Objective

Delete stale worker launch residue and unused compatibility plumbing left after
the generic worker substrate migration.

## Scope

- `novaic-agent-runtime/task_queue/workers/{task_worker,saga_worker,health_worker,scheduler_worker}.py`
- `novaic-agent-runtime/main_novaic.py`
- active root/app start scripts if CLI arguments are removed
- residue guard tests

## Expected Result

The only active runtime process entrypoint is `main_novaic.py` through the
shared process runner. Worker business classes no longer accept or store unused
gateway/broadcast inputs. Tests and static guards prove the old module helpers
and obsolete lifecycle shapes are gone.

## Verification

- Targeted worker tests.
- Residue guard tests.
- Full runtime `pytest -q`.
- Compileall for changed Python modules.

## Execution Notes

- Started 2026-05-07.
- Deleted retired `main_task.py` and `main_saga.py`.
- Inlined Saga worker assembly into `main_novaic.py`.
- Removed stale worker args from root/app start scripts and runtime spec.

## Result

- Completed. See `../results/R000-physical-residue-cleanup.md`.

## Check

- Completed. See `../checks/C000-physical-residue-cleanup.md`.
