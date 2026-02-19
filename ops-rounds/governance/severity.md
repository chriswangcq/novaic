# Severity Definition

- `P0`: release-blocking, data loss/corruption risk, startup or healthcheck failure, or critical contract breakage
- `P1`: major functional risk, significant test gap, or unstable behavior under common scenarios
- `P2`: non-blocking improvement, documentation gap, or optimization item

## Decision Rules
- Any open `P0` => round result is `FAIL`
- More than 3 open `P1` => round result is `CONDITIONAL_PASS`
- No open `P0` and <=3 open `P1` => round result can be `PASS`
