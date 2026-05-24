# Bootstrap API-host worktree and redeploy controller

## Problem

The API host has the release-controller deployed, but real release commands need `/opt/novaic/release-controller/worktree` to be a managed git checkout with submodules. Bootstrap or repair that checkout, then redeploy the updated release-controller image.

## Success Criteria

- API-host worktree is a git checkout for `https://github.com/chriswangcq/novaic.git`.
- Submodules needed by the backend and Factory build contexts are initialized.
- Release-controller image is rebuilt, pushed to the API-host registry, and deployed by immutable digest.
- Deployed controller remains loopback-only and healthy.
- Deployed controller can observe branch heads using its configured repo/worktree.
- Existing prod/staging API and Factory health checks still pass.
