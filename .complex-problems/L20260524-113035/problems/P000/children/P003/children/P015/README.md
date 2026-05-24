# Add release-controller deploy script path

## Problem

Add image-based deploy support for the release-controller so deployment can pull/run an immutable controller image without rebuilding on the production host.

## Success Criteria

- `deploy` has a clear image-based release-controller command.
- The command rejects mutable image refs for non-local deployment.
- The command preserves existing `services-image` and `factory-image` behavior.
- Shell syntax validation passes.
- Local dry validation or help output documents the new command.
