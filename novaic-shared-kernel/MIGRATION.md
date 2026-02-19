# Shared Kernel Migration Guide (Week 1)

## Install

```bash
pip install -e ./novaic-shared-kernel
```

## Import Target

Keep imports stable:

```python
from common.config import ServiceConfig
from common.exceptions import ValidationError
```

## Round 002 Progress

- Core modules are now package-native under `src/common`:
  - `config`, `strict_config`, `exceptions`, `enums`
  - `db/*`, `http/*`, `utils/time.py`
- Remaining modules still resolve via fallback bridge during transition.

## Remaining Target

- Complete migration of all shared modules into package source.
- Remove fallback bridge from `common/__init__.py`.
- Repositories consume immutable package artifacts instead of local source path.
