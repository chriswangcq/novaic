# P009: Task and saga engines use effect adapters

## Problem
Task and saga engines use effect adapters

## Success Criteria
- TaskExecutionEngine and SagaLaunchEngine no longer hold direct queue/saga/business clients; adapters execute explicit effects
