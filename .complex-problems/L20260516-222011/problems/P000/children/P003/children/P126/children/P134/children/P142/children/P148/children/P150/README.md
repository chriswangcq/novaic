# Runtime bridge step request shape audit

## Problem

Runtime-side code that sends step records to Cortex must construct the new structured observation/payload_ref shape. If it emits old inline result shapes, Cortex may reject active agent loops or lose payload refs.

This belongs under `P148` because active projection correctness depends on the producer as well as the Cortex endpoint.

## Success Criteria

- Runtime/Cortex bridge call sites that publish tool step records are mapped.
- Produced request shape contains `observation`, `step_ref`, and `payload_ref` where applicable.
- No runtime call site sends inline raw `result` as the durable tool result.
- Focused tests or source evidence prove the runtime producer uses the new contract.
