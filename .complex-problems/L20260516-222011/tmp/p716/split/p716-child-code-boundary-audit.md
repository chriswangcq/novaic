# Business/subscriber code dependency boundary audit

## Problem

Audit Business/subscriber active code for hidden env/config reads or ownership leaks that contradict the explicit dependency boundary, especially around subscriber aggregation config and dispatch behavior. This belongs under P716 because code-level residue would be higher impact than doc residue and must be proven clean or patched.

## Success Criteria

- Active subscriber aggregation path is checked for dynamic `os.environ` reads inside business decisions.
- Business/subscriber code paths are checked for direct wake/session/Cortex lifecycle ownership leakage.
- Safe code residue is patched if found.
- Test-only environment reads or fixtures are classified and not mistaken for production hidden inputs.
- If code remediation is not needed, the result cites exact evidence.
