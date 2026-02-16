# Tools Server QEMU Contract

## Response Semantics

Internal QEMU endpoints may return **HTTP 200** even when the operation fails. Failure is indicated at the **body level** via `{success: false, error: "..."}`. The executor **must not** rely on HTTP status code alone; it must parse the response body for `success` and `error` fields.

## Inferred-Success Fallback

When the `success` field is **missing** from the JSON body, treat the result as:

- **Success** if `error` is absent or empty
- **Failure** if `error` is present and non-empty

## Response Examples

### Success

```json
{
  "success": true,
  "stdout": "command output",
  "exit_code": 0
}
```

### Failure (HTTP 200 with body-level error)

```json
{
  "success": false,
  "error": "VM not running or not found"
}
```

## Relevant Tools

- `qemu_ssh_exec`
- `qemu_status`
- `qemu_start_vm`
- `qemu_restart_vm`
- `qemu_shutdown_vm`

## Testing

See `tests/unit/tools_server/test_executor_qemu_contract.py` for contract tests.
