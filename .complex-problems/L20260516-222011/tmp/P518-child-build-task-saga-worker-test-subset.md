# Build Task Saga Worker Test Subset

## Problem

Construct the P518 task/saga/worker focused pytest target list from the P513 selected focused test inventory without accidentally including non-test files or omitting obvious task/saga/worker/FSM/control-plane coverage.

## Success Criteria

- The generated list contains only existing `test_*.py` files.
- The selection command and filter terms are recorded.
- Inclusion and exclusion counts are recorded.
- Obvious task/saga/worker/FSM/control-plane terms from the P518 problem statement are represented or explicitly explained.
