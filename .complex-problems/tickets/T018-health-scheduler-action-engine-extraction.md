# T018: Health/Scheduler Action Engine Extraction

Status: done
Problem: P018

## Objective

Extract health recovery and scheduled wake action engines from business
handler modules.

## Scope

- `task_queue/workers/health_worker.py`
- `task_queue/workers/scheduler_worker.py`
- new action engine modules if needed.
- component assembly and tests.

## Expected Result

Health/scheduler handlers become tick-job DSL adapters over injected action
engines.

## Verification

- Static guard: no HTTP/client/assembler construction in health/scheduler
  handler modules.
- Health/scheduler tests.
- Full runtime tests.
