# CI Templates (Week 1)

Reusable GitHub Actions workflows maintained by Platform Team.

## Templates

- `python-service.yml`
- `rust-service.yml`
- `frontend-app.yml`

## Usage Example

```yaml
name: Service CI

on:
  pull_request:
  push:
    branches: [main]

jobs:
  ci:
    uses: ./.github/ci-templates/python-service.yml
    with:
      service_path: novaic-backend
      python_version: "3.11"
      test_command: "pytest -q tests/unit"
```

## Compatibility Policy

Each consuming workflow should align with `compatibility.yaml` for runtime
versions and approved toolchains.
