# Release-controller discovery and architecture design

## Problem

Before implementation, define the release-controller architecture against the current NovAIC deploy substrate, API-host runtime, branch strategy, registry choice, security boundary, state model, and failure behavior.

## Success Criteria

- Current deploy/runtime substrate is inventoried.
- Branch-to-environment rules are explicit.
- Controller state model and run lifecycle are documented.
- Security boundaries for Docker socket, git access, deploy commands, and prod promotion are explicit.
- The design names what will remain outside the controller, especially nginx and service discovery.
