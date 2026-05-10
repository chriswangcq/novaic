# Device tools not mounted for 小马

## Problem

Investigate why 小马 does not see device tools in the LLM `tools` array even though the agent is expected to have a device binding.

The investigation must distinguish:

- whether 小马 has a device binding and mounted tools in persisted state;
- whether Business can compute the correct filtered device tools;
- whether Runtime/Cortex actually include those tools in `cortex.prepare_llm_context`;
- whether Runtime has executors for those tools if they were exposed.

## Success Criteria

- Identify the exact broken boundary with code and production evidence.
- Explain whether the failure is data/configuration, schema assembly, executor routing, or all of them.
- Record evidence in the ledger and state whether a code fix is needed.
