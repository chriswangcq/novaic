# Business/subscriber active documentation remediation

## Problem

Patch safe active stale documentation claims found by candidate disposition so Business/subscriber boundaries match the current architecture. This belongs under P716 because stale docs are the main identified remediation surface and can mislead future agents into wrong service ownership.

## Success Criteria

- Safe active stale claims about Business, Subscriber, Gateway, Entangled, Queue, Runtime, Cortex, or Device ownership are patched.
- Historical comparison text is preserved only when clearly framed as non-current behavior.
- Patched docs use current boundary language: Business owns product/domain/action hooks and internal product APIs; Subscriber drains Environment notifications into Queue; Queue owns session/task/saga FSM; Runtime executes loops; Cortex owns scope/context; Gateway is edge; Device/devicectl owns hardware actions.
- No broad compatibility claim is added.
