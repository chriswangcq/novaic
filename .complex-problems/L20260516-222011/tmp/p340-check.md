# Session-ended delivery chain inventory check

## Summary

Success. The one-go inventory produced a usable, evidence-backed map of the session-ended delivery chain and identified concrete unsafe/defaulting boundaries for P341-P344. It did not attempt implementation, which is correct for this child problem.

## Evidence

- R322 lists the live chain from `wake_finalize.py::_build_session_ended_payload` through `handle_session_ended`, `TaskQueueClient.session_ended`, `SessionEndedRequest`, and `SessionRepository.session_ended`.
- R322 identifies required payload fields at the delivery boundary: agent id, subagent id, scope id, generation, finalize reason, and remaining stack.
- R322 classifies concrete unsafe boundaries:
  - `wake_finalize.py::_session_generation(ctx)` uses `session_generation or 0`.
  - `session_handlers.py::handle_session_ended` only checks `generation is None` and casts with `int(...)`.
  - `routes.py::SessionEndedRequest` uses plain `generation: int`.
- R322 distinguishes broader upstream react defaults from the P336 delivery path and assigns them to P343/P337/P339 instead of burying them.
- R322 cites targeted `rg` searches and file reads as verification evidence.

## Criteria Map

- List every live file/function in the session-ended delivery chain: satisfied by the chain list in R322.
- Identify payload fields required at each boundary: satisfied; R322 names agent/subagent/scope/generation/finalize reason/remaining stack and classifies where they are preserved or weak.
- Classify each boundary as safe, unsafe, or test-only: satisfied; R322 marks repository safe after P335, wake-finalize unsafe, handler/route incomplete, tests existing, and upstream react defaults delegated.
- Produce concrete implementation targets for remaining children: satisfied; R322 assigns work to P341, P342, P343, and P344.

## Execution Map

- Read-only inspection was performed on saga, handler, client, route, react contracts, and tests.
- No code mutation was performed in P340.
- The result directly feeds the next runnable child problems under P336.

## Stress Test

- Checked for the plausible hidden-residue failure where the visible delivery payload includes a generation field, but one upstream builder still fills it with `0`. R322 found that exact residue in `wake_finalize.py` and broader react contracts.
- Checked for the plausible validation-gap failure where the handler or route accepts zero even though repository now rejects it. R322 found both weak boundaries.

## Residual Risk

- Non-blocking for P340: the inventory did not fix the unsafe paths; P341-P344 exist for that.
- Non-blocking for P340: additional hidden generation defaults may exist outside P336's delivery path; P343/P337/P339 will handle broader compatibility residue.

## Result IDs

- R322
