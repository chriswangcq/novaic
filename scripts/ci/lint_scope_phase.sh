#!/usr/bin/env bash
#
# PR-29 (2026-04-15) — ban raw ``meta["phase"] = ...`` writes in Cortex.
#
# Why
# ---
# ``meta["phase"]`` is the authoritative state column for the Cortex scope
# state machine (see novaic-cortex/novaic_cortex/scope_state.py). A direct
# ``meta["phase"] = "archived"`` bypasses transition() — meaning:
#   * the ALLOWED matrix isn't enforced (archived → executing regressions
#     slip through silently, violating INV-6),
#   * scope_end idempotency (INV-5) stops depending on one shared helper
#     and starts depending on each caller remembering to re-check,
#   * the PR-29 canonical log line (``scope_state scope=...``) is never
#     emitted, so PR-31's scope_state_transitions table will have holes,
#   * the transition metric counter is never bumped.
#
# How
# ---
# The only legitimate writer is:
#   1. novaic-cortex/novaic_cortex/scope_state.py   (the module itself)
#   2. novaic-cortex/novaic_cortex/workspace.py     (initial_phase() on
#                                                     create_scope — the
#                                                     only non-transition
#                                                     write, guarded by
#                                                     the helper)
#   3. tests/                                        (fixtures fabricate meta
#                                                     dicts)
#   4. docs/                                         (example meta.json)
# Anything else hitting the pattern needs justification and an allowlist
# entry here. If you just need to flip phase, call
# ``novaic_cortex.scope_state.transition(...)`` (or ``mark_archived``).
set -e

# Match both forms:
#   meta["phase"] = ...        (subscript assignment)
#   "phase": "archived"       (dict literal with the terminal value)
# The second pattern is tighter — we only ban writing the *specific*
# state values, so ``"phase": existing_meta.get("phase", "executing")``
# reads stay allowed.
PATTERNS=(
    'meta\["phase"\]\s*='
    '"phase"\s*:\s*"archived"'
    '"phase"\s*:\s*"failed"'
    '"phase"\s*:\s*"compacting"'
)

ALLOWLIST=(
    'novaic-cortex/novaic_cortex/scope_state.py'
    'novaic-cortex/novaic_cortex/workspace.py'
    'tests/'
    'docs/'
    'scripts/ci/lint_scope_phase.sh'
)

violations=0
for PATTERN in "${PATTERNS[@]}"; do
    HITS=$(rg -l --pcre2 -U "$PATTERN" \
              --glob '*.py' \
              novaic-cortex 2>/dev/null || true)
    for f in $HITS; do
        ok=0
        for a in "${ALLOWLIST[@]}"; do
            [[ "$f" == *"$a"* ]] && ok=1
        done
        if [[ $ok -eq 0 ]]; then
            echo "BAN: $f writes meta.phase outside scope_state.transition()"
            echo "     pattern matched: $PATTERN"
            violations=$((violations + 1))
        fi
    done
done

if [[ $violations -gt 0 ]]; then
    echo ""
    echo "Context: PR-29 mandates novaic_cortex.scope_state.transition() as"
    echo "the only write path to meta.phase. See"
    echo "novaic-cortex/novaic_cortex/scope_state.py for the ALLOWED matrix,"
    echo "or docs/roadmap/tickets/PR-29-scope-state-machine.md for the RFC."
    exit 1
fi
echo "scope_phase lint OK"
