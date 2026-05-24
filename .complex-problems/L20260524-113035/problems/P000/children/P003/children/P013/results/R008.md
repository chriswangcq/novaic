# P013 Result

## Summary

Added Docker image packaging for the release-controller service.

## Done

- Added `docker/release-controller/Dockerfile`.
- Updated `.dockerignore` allowlist so `novaic-release-controller` is included in root Docker build context.
- Added `build-system` and setuptools package discovery metadata to `novaic-release-controller/pyproject.toml`.
- Dockerfile installs runtime tools needed by the controller command plans: `git`, `curl`, and Docker CLI package.
- Dockerfile installs the local Python package and starts `python -m release_controller.main`.
- Runtime config remains driven by `NOVAIC_RELEASE_CONTROLLER_CONFIG`.

## Verification

- `PYTHONPATH=novaic-release-controller python3 -m pytest novaic-release-controller/tests -q`
  - Passed: 31 tests.
- `python3 -m pip wheel --no-deps -w /tmp/novaic-release-controller-wheel ./novaic-release-controller`
  - Successfully built `novaic_release_controller-0.1.0-py3-none-any.whl`.
- `docker --version`
  - Docker CLI exists locally.
- `docker build -f docker/release-controller/Dockerfile -t novaic/release-controller:test .`
  - Could not run because local Docker daemon socket `/var/run/docker.sock` is unavailable.

## Known Gaps

- Real Docker image build was not completed in the local environment because the Docker daemon is not running.
- Compose integration and deploy script integration remain assigned to sibling P014 and P015.

## Artifacts

- `docker/release-controller/Dockerfile`
- `.dockerignore`
- `novaic-release-controller/pyproject.toml`
